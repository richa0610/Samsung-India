"""scripts/reset_and_seed.py (user, 2026-10-20): wipes every company's activity data and makes sample
data the way the app's own screens make it - through the API, here the app in process.

Synthetic TenantWorld (in-memory SQLite) and temporary folders only - no real database is touched."""

import io
import json
import re
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from sqlalchemy.orm import sessionmaker

from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.category import Category, SubCategory
from app.models.common.user_registry import UserRegistry
from app.models.conference import Conference
from app.models.pincode import Pincode
from app.models.quiz import AssessmentResult, AssessmentSuite, Question
from app.models.trainee import Trainee
from app.models.uid_sequence import UidSequence
from app.models.venue import Venue
from app.services import user_registry_service as registry_service
from app.utils import uid as uid_utils
from scripts import reset_and_seed as reset
from tests.tenant_fixtures import ALPHA, BETA
from tests.test_trainer_authorization import TrainerWorldTestCase

PASSWORD = "Sample-Pass-42"
PHOTO = b"\xff\xd8\xff\xe0" + b"\x00" * 64


class ResetTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        real_ids = patch("app.models.uid_events.next_uid", uid_utils.next_uid)
        real_ids.start()
        self.addCleanup(real_ids.stop)
        root = Path(self.enterContext(tempfile.TemporaryDirectory()))
        for target in ("app.routers.media.MEDIA_ROOT", "app.core.media.MEDIA_ROOT"):
            self.enterContext(patch(target, root))
        self.folder = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.common = self.w.common
        self.engines = {"common": self.w.common_engine, ALPHA: self.w.alpha_engine, BETA: self.w.beta_engine}

        # The company's setup, which the reset keeps: a zone list, a question set, a venue, counters.
        for code, zone in (("N", "North"), ("S", "South")):
            self.alpha.add(Category(categoryUid=f"CAT-{code}", name=zone, visibleOnWeb="Zone", status="Approved"))
            self.alpha.add(SubCategory(subCategoryUid=f"SUB-{code}1", categoryUid=f"CAT-{code}", subCategory=f"{zone} 1",
                                       visibleOnWeb="No", status="Approved"))
        self.alpha.add(AssessmentSuite(assessmentSuiteUid="ASM-T", examTitle="Product Post Test", assessment_type="Post Test",
                                       noOfQuestion=3, status="Approved"))
        for n, correct in enumerate("abc"):
            self.alpha.add(Question(assessmentSuiteUid="ASM-T", question=f"Q{n}", correct_answer=correct, points=1, sort_order=n,
                                    options=json.dumps([{"id": o, "text": o.upper()} for o in "abc"])))
        self.alpha.add(Venue(venueUid="VEN-1", name="Main Hall", state="Delhi", district="New Delhi", zone="North", region="North 1"))
        for prefix, next_val in (("TRN", 10005), ("ASM", 10003), ("CONF", 10010)):
            self.alpha.add(UidSequence(prefix=prefix, next_val=next_val))
        self.alpha.commit()
        self.common.add(Pincode(pincode=110001, district="New Delhi", stateName="Delhi"))
        self.common.commit()
        registry_service.reconcile_tenant(self.common, self.alpha, ALPHA)

    def count(self, db, model, **filters):
        db.expire_all()
        return db.query(model).filter_by(**filters).count()

    def counters(self):
        self.alpha.expire_all()
        return sorted(p for (p,) in self.alpha.query(UidSequence.prefix))


class TheDryRun(ResetTestCase):
    def test_it_lists_what_goes_and_writes_nothing(self):
        before = {label: reset.table_counts(engine) for label, engine in self.engines.items()}
        out = io.StringIO()
        with redirect_stdout(out):
            reset.print_plan(self.engines)
        self.assertRegex(out.getvalue(), r"delete:.*trainee=")
        self.assertIn("counters CONF, TRN", out.getvalue())   # ASM's stays: the question sets do
        self.assertEqual({label: reset.table_counts(engine) for label, engine in self.engines.items()}, before)


class BackupWipeAndRestore(ResetTestCase):
    def test_the_wipe_empties_the_activity_and_keeps_the_setup(self):
        kept = {model: self.count(self.alpha, model) for model in (Category, AssessmentSuite, Question, Venue)}
        self.assertGreater(self.count(self.alpha, Trainee), 0)
        reset.wipe_company(self.w.alpha_engine)
        reset.wipe_common(self.w.common_engine)
        for model in (Trainee, AgencyTeam, Conference, Attendance, AssessmentResult):
            self.assertEqual(self.count(self.alpha, model), 0, model.__name__)
        self.assertEqual(self.count(self.common, UserRegistry), 0)
        self.assertEqual({model: self.count(self.alpha, model) for model in kept}, kept)
        self.assertEqual(self.counters(), ["ASM"])
        self.assertGreater(self.count(self.w.tenant_db[BETA], Trainee), 0)   # another company's wipe is its own

    def test_restore_puts_back_every_table_the_wipe_changed(self):
        before = {label: reset.table_counts(engine) for label, engine in self.engines.items()}
        reset.back_up(self.engines, self.folder)
        reset.wipe_company(self.w.alpha_engine)
        reset.wipe_common(self.w.common_engine)
        reset.restore(self.engines, self.folder)
        self.assertEqual({label: reset.table_counts(engine) for label, engine in self.engines.items()}, before)
        self.assertEqual(self.counters(), ["ASM", "CONF", "TRN"])


class AfterTheWipe(ResetTestCase):
    def test_what_the_sample_reuses_reads_the_same_from_the_backup(self):
        self.alpha.query(AgencyTeam).filter_by(username="trainer1").update({"companyUid": "CMP26001"})
        self.alpha.query(Conference).update({"audience": "Retail Sales Executives"})
        self.alpha.commit()
        open_tenant = lambda uid: sessionmaker(bind=self.engines[uid])()
        before = reset.companies(self.common, open_tenant)
        reset.back_up(self.engines, self.folder)
        reset.wipe_company(self.w.alpha_engine)
        after = reset.companies(self.common, open_tenant, backup=self.folder)
        self.assertEqual([(c.tenant_uid, c.company_uid, c.options) for c in after],
                         [(c.tenant_uid, c.company_uid, c.options) for c in before])
        self.assertEqual((after[0].company_uid, after[0].options["audience"]), ("CMP26001", "Retail Sales Executives"))


class DropdownLists(ResetTestCase):
    def test_a_company_without_lists_gets_the_default_company_s_with_their_ids_and_counters(self):
        beta = self.w.tenant_db[BETA]
        beta.query(SubCategory).delete()
        beta.query(Category).delete()
        beta.commit()
        self.alpha.add(UidSequence(prefix="CAT", next_val=10009))
        self.alpha.commit()

        copied = reset.copy_lists(self.w.alpha_engine, self.w.beta_engine)
        self.assertEqual(copied, {"category": self.count(self.alpha, Category), "subcategory": self.count(self.alpha, SubCategory)})
        beta.expire_all()
        names = lambda db: sorted((c.categoryUid, c.name, c.visibleOnWeb) for c in db.query(Category))
        self.assertEqual(names(beta), names(self.alpha))
        self.assertEqual(sorted((s.subCategoryUid, s.categoryUid) for s in beta.query(SubCategory)),
                         sorted((s.subCategoryUid, s.categoryUid) for s in self.alpha.query(SubCategory)))
        self.assertEqual(beta.query(UidSequence).filter_by(prefix="CAT").one().next_val, 10009)   # new ones won't repeat them

    def test_a_company_with_lists_of_its_own_keeps_them(self):
        self.assertEqual(reset.copy_lists(self.w.beta_engine, self.w.alpha_engine), {})
        self.assertEqual(self.count(self.alpha, Category, name="North"), 1)


class TheSample(ResetTestCase):
    def setUp(self):
        super().setUp()
        company = reset.companies(self.common, lambda uid: sessionmaker(bind=self.engines[uid])())[0]
        self.assertEqual(company.tenant_uid, ALPHA)
        reset.wipe_company(self.w.alpha_engine)
        reset.wipe_common(self.w.common_engine)
        self.seeder = reset.Seeder(
            self.w.client, sessionmaker(bind=self.w.common_engine), lambda uid: sessionmaker(bind=self.engines[uid])(),
            PASSWORD, PHOTO,
        )
        self.seeder.seed(company)

    def test_trainers_trainees_and_their_registry_rows(self):
        year = f"{uid_utils.ist_now().year % 100:02d}"
        self.alpha.expire_all()
        trainers = self.alpha.query(AgencyTeam).order_by(AgencyTeam.id).all()
        self.assertEqual([t.agencyTeamUid for t in trainers], [f"AGT{year}10001", f"AGT{year}10002"])
        self.assertEqual({(t.role, t.status, t.company) for t in trainers}, {("trainer", "Approved", "Samsung India")})

        trainees = self.alpha.query(Trainee).all()
        self.assertEqual(len(trainees), 10)
        self.assertTrue(all(re.fullmatch(rf"(NORTH|SOUTH){year}\d{{5}}", t.traineeUid) for t in trainees), [t.traineeUid for t in trainees])
        self.assertEqual(sum(1 for t in trainees if t.password), reset.TRAINEES_BY_FORM)   # self sign-ups have none

        self.common.expire_all()
        entries = self.common.query(UserRegistry).all()
        self.assertEqual(len(entries), 12)
        self.assertEqual({(e.tenant_uid, e.status) for e in entries}, {(ALPHA, "active")})
        self.assertTrue(all(e.devices for e in entries if e.user_uid.startswith("AGT")))   # signed in through the API

    def test_two_trainings_ran_end_to_end_and_two_are_scheduled(self):
        self.alpha.expire_all()
        trainings = self.alpha.query(Conference).order_by(Conference.id).all()
        self.assertEqual([t.status for t in trainings], ["Approved"] * 4)
        self.assertEqual([t.conferenceStatus for t in trainings][2:], ["Scheduled", "Scheduled"])
        finished = [t.conferenceUid for t in trainings[:2]]
        for uid in finished:
            self.assertEqual(self.count(self.alpha, Attendance, conferenceUid=uid, status="Present"), reset.PRESENT_PER_TRAINING)
            self.assertEqual(self.count(self.alpha, AssessmentResult, conferenceUid=uid), reset.PRESENT_PER_TRAINING)
        self.assertNotIn(trainings[0].conferenceStatus, ("Scheduled", "Started", "Ongoing"))
        self.assertEqual([kind for _c, _uid, kind in self.seeder.report.trainings], ["finished", "finished", "scheduled", "scheduled"])

    def test_the_accounts_file_names_everyone_and_the_password(self):
        path = reset.write_accounts(self.folder, PASSWORD, self.seeder.report)
        text = path.read_text(encoding="utf-8")
        self.assertIn(PASSWORD, text)
        self.assertEqual(text.count("(self sign-up, no password)"), reset.TRAINEES_SELF)
        self.assertIn("aarav.sharma", text)


class EachCompanyHasItsOwnPeople(ResetTestCase):
    def test_the_second_company_s_people_follow_the_first_s(self):
        size = reset.TRAINERS + reset.TRAINEES_BY_FORM + reset.TRAINEES_SELF
        first = reset.Seeder.people_for(reset.Company(ALPHA, "A", None, 0))
        second = reset.Seeder.people_for(reset.Company(BETA, "B", None, 1))
        self.assertEqual((len(first), len(second)), (size, size))
        self.assertFalse({p.username for p in first} & {p.username for p in second})
        self.assertEqual(second[0].username, reset.Person(*reset.PEOPLE[size]).username)


class TheWindows(ResetTestCase):
    def test_late_in_the_day_the_windows_stay_inside_it(self):
        from datetime import datetime

        start, attendance, test = reset.Seeder.windows(datetime(2026, 10, 20, 23, 50))
        self.assertEqual((start, attendance["checkInOpens"], attendance["checkOutCloses"], test["endTime"]),
                         ("11:50 PM", "11:45 PM", "11:58 PM", "11:59 PM"))

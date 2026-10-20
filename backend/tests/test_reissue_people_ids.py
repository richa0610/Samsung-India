"""scripts/reissue_people_ids.py (user, 2026-10-20): gives a company's people IDs and HO IDs no other
company uses, so they can join the central user registry - the demo company's repeated Samsung's.
BETA plays the demo company here, ALPHA the company whose IDs it repeats.

Synthetic TenantWorld (in-memory SQLite) and a temporary backup folder only."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from app.core.config import settings
from app.database.tenant import tenant_manager
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.quiz import AssessmentResult
from app.models.trainee import Trainee
from app.services import user_registry_service as registry_service
from app.utils import uid as uid_utils
from scripts import reissue_people_ids as reissue
from tests.tenant_fixtures import ALPHA, BETA
from tests.test_trainer_authorization import TrainerWorldTestCase


class ReissueTestCase(TrainerWorldTestCase):
    def setUp(self):
        super().setUp()
        real_ids = patch("app.models.uid_events.next_uid", uid_utils.next_uid)
        real_ids.start()
        self.addCleanup(real_ids.stop)
        self.common, self.beta = self.w.common, self.w.tenant_db[BETA]
        # ALPHA already uses these numbers; BETA repeats them (as Demo repeated Samsung).
        self.alpha.add(Trainee(traineeUid="TRN2610007", name="A", email="a7@example.test", phone=9_300_000_007, employee_id="EMP26007"))
        self.alpha.add(AgencyTeam(agencyTeamUid="AGT2610005", username="alpha.trainer", password="x", role="trainer", offerId="OFF26005"))
        self.alpha.commit()
        for model in (Attendance, AssessmentResult):   # nothing recorded against BETA's old IDs
            self.beta.query(model).delete()
        self.beta.add(Trainee(traineeUid="TRN2610007", name="B", email="b7@example.test", phone=9_400_000_007, employee_id="EMP26007"))
        self.beta.add(AgencyTeam(agencyTeamUid="AGT2610005", username="beta.trainer", password="x", role="trainer", offerId="OFF26005"))
        self.beta.commit()
        self.backups = Path(tempfile.mkdtemp())

    def open_tenant(self, tenant_uid):
        return tenant_manager.get_session(tenant_uid, self.common)

    def alpha_uids(self):
        return {uid for (uid,) in self.alpha.query(Trainee.traineeUid)} | {uid for (uid,) in self.alpha.query(AgencyTeam.agencyTeamUid)}


class TheDryRun(ReissueTestCase):
    def test_new_ids_start_above_every_company_s_numbers_and_nothing_is_written(self):
        before = [(t.traineeUid, t.employee_id) for t in self.beta.query(Trainee).order_by(Trainee.id)]
        changes = reissue.plan_reissue(self.common, self.beta, BETA, self.open_tenant)
        self.common.rollback()
        by_old = {change.old_uid: change for change in changes}
        self.assertEqual(by_old["AGT2610005"].new_uid, f"AGT{uid_utils.ist_now().year % 100:02d}10006")
        self.assertEqual(by_old["TRN2610007"].new_hoid, "BETA-EMP-003")
        self.assertFalse({change.new_uid for change in changes} & self.alpha_uids())
        self.beta.expire_all()
        self.assertEqual([(t.traineeUid, t.employee_id) for t in self.beta.query(Trainee).order_by(Trainee.id)], before)
        self.assertEqual(self.common.execute(reissue.text("SELECT COUNT(*) FROM uid_sequence")).scalar(), 0)


class Applying(ReissueTestCase):
    def test_the_people_get_the_planned_ids_a_backup_is_kept_and_the_registry_takes_them_all(self):
        planned = reissue.plan_reissue(self.common, self.beta, BETA, self.open_tenant)
        self.common.rollback()
        changes, backup = reissue.apply_reissue(self.common, self.beta, BETA, self.open_tenant, self.backups)
        self.assertEqual([c.new_uid for c in changes], [c.new_uid for c in planned])

        self.beta.expire_all()
        trainer = self.beta.query(AgencyTeam).filter_by(username="beta.trainer").one()
        self.assertEqual((trainer.agencyTeamUid, trainer.offerId), (changes[-1].new_uid, "BETA-OFF-001"))
        saved = json.loads(backup.read_text(encoding="utf-8"))
        self.assertIn({"table": "agencyteam", "old_uid": "AGT2610005", "old_hoid": "OFF26005"},
                      [{k: c[k] for k in ("table", "old_uid", "old_hoid")} for c in saved["changes"]])

        registry_service.reconcile_tenant(self.common, self.alpha, ALPHA)
        report = registry_service.reconcile_tenant(self.common, self.beta, BETA)
        self.assertEqual(report.skipped, [])

    def test_undo_puts_back_the_old_ids_on_rows_unchanged_since(self):
        changes, backup = reissue.apply_reissue(self.common, self.beta, BETA, self.open_tenant, self.backups)
        moved = self.beta.query(Trainee).filter_by(traineeUid=changes[0].new_uid).one()
        moved.traineeUid = "CHANGED-SINCE"
        self.beta.commit()
        restored = reissue.undo_reissue(self.beta, json.loads(backup.read_text(encoding="utf-8")))
        self.assertEqual(restored, len(changes) - 1)
        self.beta.expire_all()
        self.assertEqual(self.beta.query(AgencyTeam).filter_by(username="beta.trainer").one().agencyTeamUid, "AGT2610005")


class WhatIsRefused(ReissueTestCase):
    def test_the_default_company(self):
        with patch.object(settings, "DEFAULT_TENANT_ID", BETA), self.assertRaises(SystemExit):
            reissue.plan_reissue(self.common, self.beta, BETA, self.open_tenant)

    def test_a_company_with_attendance_recorded_against_the_old_ids(self):
        with self.assertRaises(SystemExit):
            reissue.plan_reissue(self.common, self.alpha, ALPHA, self.open_tenant)   # ALPHA has attendance

    def test_a_new_ho_id_another_company_already_holds(self):
        self.common.add(registry_service.UserRegistry(tenant_uid=ALPHA, user_type="trainee", user_uid="X1", hoid="beta-emp-001", status="active"))
        self.common.commit()
        with self.assertRaises(SystemExit):
            reissue.plan_reissue(self.common, self.beta, BETA, self.open_tenant)

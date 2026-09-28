"""Shared synthetic "world" for the multi-tenant access tests (Phase C).

Two isolated in-memory tenant databases (ALPHA, BETA) plus a shared ("common") database, all
SQLite, all synthetic - never a real database (tests/__init__.py forces an unusable address).

ALPHA holds two companies. Zones / regions repeat across companies on purpose, so a test can
tell a company boundary apart from a zone boundary. BETA also has a company named
"Samsung India", so a test can tell the tenant boundary apart from the company text.

    ALPHA  Samsung India  North Zone  North 1     S_N1        trainer1
                                      Delhi NCR   S_DEL       trainer1
                          South Zone  South 1     S_S1        trainer2
                          (blank zone/region)     S_BLANK     trainer2
                          " samsung india " / "north zone " / "north 1"  S_N1V (spelling variant) trainer1
           Other Co       North Zone  North 1     O_N1        trainer3
    BETA   Samsung India  North Zone  North 1     B_N1        trainer_b

Accounts (all in the shared database unless noted) and the grants they hold:
    super      Super Admin                     (global)
    coadmin    Company Admin (the ONE for it)  ALPHA / Samsung India
    coord      Coordinator                     ALPHA / Samsung India / North Zone
    subcoord   Sub-coordinator                 ALPHA / Samsung India / region Delhi NCR
    ungranted  looks like an admin, NO grant   -> must be denied
    betaonly   Company Admin                   BETA  / Samsung India (not a member of ALPHA)
    adm_trainer  trainer stored in the admin table, trainer grant on ALPHA
    trainer1..3  agency-team trainers inside ALPHA (implicit ALPHA members)
"""

from datetime import datetime
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.database.common import get_common_db
from app.database.connection import CommonBase, TenantBase
from app.database.tenant import tenant_manager
from app.models import *  # noqa: F401,F403 - registers every table
from app.models.admin import Admin
from app.models.admin_access import AccessBase, AdminAccess
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.common.tenant_registry import Tenant
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.services.access_service import company_admin_key
from app.models.trainee import Trainee

ALPHA, BETA = "ALPHA", "BETA"
PASSWORD = "Correct-Horse-9"

# (key, tenant, company, zone, region, trainer)
CONFERENCES = [
    ("S_N1", ALPHA, "Samsung India", "North Zone", "North 1", "trainer1"),
    ("S_DEL", ALPHA, "Samsung India", "North Zone", "Delhi NCR", "trainer1"),
    ("S_S1", ALPHA, "Samsung India", "South Zone", "South 1", "trainer2"),
    ("S_BLANK", ALPHA, "Samsung India", None, None, "trainer2"),
    ("S_N1V", ALPHA, " samsung india ", "north zone ", "north 1", "trainer1"),
    ("O_N1", ALPHA, "Other Co", "North Zone", "North 1", "trainer3"),
    ("B_N1", BETA, "Samsung India", "North Zone", "North 1", "trainer_b"),
]


def uid(key: str) -> str:
    return f"CONF-{key}"


class TenantWorld:
    """Builds the world once per test (cheap: in-memory) and tears it down."""

    def __init__(self):
        mem = lambda: create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self.common_engine, self.alpha_engine, self.beta_engine = mem(), mem(), mem()
        self._patches = [
            patch("app.models.uid_events.next_uid", lambda connection, prefix: None),
            # A WebSocket handshake (app/routers/ws.py) and a couple of training_service lookups
            # aren't part of the FastAPI Depends graph, so app.dependency_overrides[get_common_db]
            # below can't reach them - they do their own local `from app.database.common import
            # CommonSessionLocal` instead, which this patches to the same synthetic common DB
            # every other part of this world already uses (without it, they'd quietly try to
            # open the real, forced-unusable common DB from tests/__init__.py).
            patch("app.database.common.CommonSessionLocal", sessionmaker(bind=self.common_engine)),
        ]
        for p in self._patches:
            p.start()

        CommonBase.metadata.create_all(self.common_engine)
        AccessBase.metadata.create_all(self.common_engine)
        TenantBase.metadata.create_all(self.alpha_engine)
        TenantBase.metadata.create_all(self.beta_engine)
        self.common = sessionmaker(bind=self.common_engine)()
        self.tenant_db = {ALPHA: sessionmaker(bind=self.alpha_engine)(), BETA: sessionmaker(bind=self.beta_engine)()}

        for tenant in (ALPHA, BETA):
            self.common.add(Tenant(tenant_uid=tenant, company_name=f"{tenant} Corp", database_host="h", database_port=3306,
                                   database_name=tenant.lower(), database_username="u", database_password="p", status="active"))
        self._seed_accounts()
        self._seed_data()
        tenant_manager.register_engine(ALPHA, self.alpha_engine)
        tenant_manager.register_engine(BETA, self.beta_engine)

        from app.main import app  # safe: TESTING is forced, so importing does no database work

        self.app = app
        app.dependency_overrides[get_common_db] = lambda: (yield self.common)
        self.client = TestClient(app, raise_server_exceptions=False)

    # ------------------------------------------------------------------ accounts
    def _seed_accounts(self):
        def admin(username, role, company=None):
            row = Admin(adminUid=f"a-{username}", username=username, name=username.title(), password=hash_password(PASSWORD),
                        role=role, company=company)
            self.common.add(row)
            self.common.flush()
            return row

        def grant(row, role, tenant=None, company=None, zone=None, region=None, active=1):
            key = company_admin_key(tenant, company) if role == "company_admin" and active else None
            self.common.add(AdminAccess(admin_id=row.id, role=role, tenant_uid=tenant, company=company, zone=zone, region=region,
                                        active=active, granted_by="fixture", company_admin_key=key))

        self.admins = {
            "super": admin("super", "admin"),
            "coadmin": admin("coadmin", "admin", "Samsung India"),
            "coord": admin("coord", "admin", "Samsung India"),
            "subcoord": admin("subcoord", "admin", "Samsung India"),
            "ungranted": admin("ungranted", "admin", "Samsung India"),
            "betaonly": admin("betaonly", "admin", "Samsung India"),
            "adm_trainer": admin("adm_trainer", "trainer"),
        }
        grant(self.admins["super"], "super_admin")
        grant(self.admins["coadmin"], "company_admin", ALPHA, "Samsung India")
        grant(self.admins["coord"], "coordinator", ALPHA, "Samsung India", zone="North Zone")
        grant(self.admins["subcoord"], "sub_coordinator", ALPHA, "Samsung India", region="Delhi NCR")
        grant(self.admins["betaonly"], "company_admin", BETA, "Samsung India")
        grant(self.admins["adm_trainer"], "trainer", ALPHA)
        self.common.commit()
        self.grant = grant

        alpha = self.tenant_db[ALPHA]
        self.agency = {}
        for n, name in enumerate(("trainer1", "trainer2", "trainer3"), start=1):
            row = AgencyTeam(agencyTeamUid=f"g{n}", username=name, name=name.title(), password=hash_password(PASSWORD), role="trainer",
                             company="Samsung India" if n < 3 else "Other Co", offerId=f"OFF{n}")
            alpha.add(row)
            self.agency[name] = row
        alpha.commit()

    # ---------------------------------------------------------------------- data
    def _seed_data(self):
        self.trainees = {}
        self.attendance_ids = {}
        stamp = datetime(2026, 9, 20, 10, 0)
        n = 0
        for key, tenant, company, zone, region, trainer in CONFERENCES:
            db = self.tenant_db[tenant]
            db.add(Conference(conferenceUid=uid(key), company=company, zone=zone, region=region, trainerEmployeeId=trainer,
                              trainerName=trainer.title(), conferenceDate="2026-09-20", conferenceStatus="Scheduled", status="Pending",
                              trainingType="Webinar", postAssessmentUid="SUITE-1", suiteTitle=f"Training {key}"))
            for i in range(2):
                n += 1
                tuid = f"TR-{key}-{i}"
                db.add(Trainee(traineeUid=tuid, name=f"Person {key} {i}", email=f"{tuid.lower()}@example.test", phone=9_000_000_000 + n,
                               username=f"user{n}", employee_id=f"HO-{key}-{i}", company=(company or "").strip(), zone=(zone or "").strip() or None,
                               region=region, trainerEmployeeId=trainer))
                db.add(Attendance(attendanceUid=f"ATT-{key}-{i}", conferenceUid=uid(key), traineeUid=tuid, status="Present" if i == 0 else "Pending",
                                  timestamp=stamp))
                if i == 0:
                    db.add(AssessmentResult(resultUid=f"RES-{key}", conferenceUid=uid(key), traineeUid=tuid, assessmentSuiteUid="SUITE-1",
                                            attemptNumber=1, totalScore=7, maxScore=10, percentage=70, status="Submitted"))
                self.trainees[tuid] = (tenant, key)
        alpha = self.tenant_db[ALPHA]
        # trainer assignment cases (all Samsung North, ALPHA):
        #   assigned by column only, no attendance   -> visible to trainer1
        #   assigned to trainer2 but ON trainer1's training -> visible to trainer1 (roster)
        #   assigned to trainer2 only                -> NOT visible to trainer1
        alpha.add(Trainee(traineeUid="TR-ASSIGNED-ONLY", name="Assigned Only", email="ao@example.test", phone=9_100_000_001, username="ao",
                          employee_id="HO-AO", company="Samsung India", zone="North Zone", region="North 1", trainerEmployeeId="trainer1"))
        alpha.add(Trainee(traineeUid="TR-ROSTER-ONLY", name="Roster Only", email="ro@example.test", phone=9_100_000_002, username="ro",
                          employee_id="HO-RO", company="Samsung India", zone="North Zone", region="North 1", trainerEmployeeId="trainer2"))
        alpha.add(Attendance(attendanceUid="ATT-RO", conferenceUid=uid("S_N1"), traineeUid="TR-ROSTER-ONLY", status="Pending", timestamp=stamp))
        alpha.add(Trainee(traineeUid="TR-OTHER-TRAINER", name="Other Trainer", email="ot@example.test", phone=9_100_000_003, username="ot",
                          employee_id="HO-OT", company="Samsung India", zone="North Zone", region="North 1", trainerEmployeeId="trainer2"))
        for db in self.tenant_db.values():
            db.commit()

    # ----------------------------------------------------------------- utilities
    def token(self, who: str, tenant: str = ALPHA) -> str:
        """A valid signed token for a seeded account, in the given tenant."""
        if who in self.admins:
            row = self.admins[who]
            return create_access_token(subject=f"admin:{row.username}", tenant_id=tenant, role=row.role)
        return create_access_token(subject=f"agencyteam:{who}", tenant_id=tenant, role="trainer")

    def headers(self, who: str, tenant: str = ALPHA) -> dict:
        return {"Authorization": f"Bearer {self.token(who, tenant)}"}

    def principal(self, who: str):
        return self.admins[who] if who in self.admins else self.agency[who]

    def conference_keys(self, items) -> set:
        """Map response items (any shape carrying a conference uid) back to fixture keys."""
        out = set()
        for item in items:
            value = item.get("conferenceUid") or item.get("conferenceId")
            out.add(str(value).removeprefix("CONF-"))
        return out

    def close(self):
        self.app.dependency_overrides.clear()
        for tenant in (ALPHA, BETA):
            tenant_manager._engines.pop(tenant, None)
            tenant_manager._sessionmakers.pop(tenant, None)
        for p in self._patches:
            p.stop()

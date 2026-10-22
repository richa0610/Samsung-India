"""Wipes the activity data of every company and fills them with sample data made the way the app's
own screens make it (user, 2026-10-20), so the Common DB and every company's DB hold one consistent
format.

KEPT: the company list, admin accounts and their access, agencies, pincodes and modules (Common DB);
the zone / region lists, question sets, venues and admin zone scopes (each company).
WIPED: user_registry (Common DB); trainees, trainers, trainings, attendance, answers, results, logs
and the ID counters of those (each company) - so new IDs start again at 10001. It also finishes the
registry clean-up of the same day: user_registry's user_type / created_at / updated_at columns and
the Common DB's login_sessions and uid_sequence tables go. A company with no dropdown lists of its own
(zones and regions, audiences, ...) gets the default company's, so every company's forms match.

SAMPLE, per company, through the server's API - the requests the app sends:
  2 trainers - inserted as the PHP system inserts them (the app has no trainer form), then added to
    user_registry;
  10 trainees - 6 through a trainer's Add Trainee form, 4 through the app's own sign-up;
  4 trainings through a trainer's Add Training form, approved as the company's admin approves them
    (that one step runs here, against the database - an admin's password isn't needed); 2 run today
    end to end (start with a photo, trainees join by the QR code, check in, take the test, end with a
    photo and the attendance sheet) and 2 are scheduled for next week.
The sample accounts share one generated password, written with their usernames to
sample-accounts.txt in the backup folder - never printed.

DRY RUN by default: reads only and prints what would be deleted and kept. --apply backs every table
of every database up to backend/backups/reset-<time>/ first. --restore <that folder> puts back every
table the reset changed.

    cd backend
    venv/Scripts/python.exe scripts/reset_and_seed.py
    venv/Scripts/python.exe scripts/reset_and_seed.py --apply
    venv/Scripts/python.exe scripts/reset_and_seed.py --restore backups/reset-20261020-230000
    venv/Scripts/python.exe scripts/reset_and_seed.py --seed-only backups/reset-20261020-230000

--seed-only makes just the sample, after a wipe whose sample didn't finish: refused unless the
activity tables are empty; what it reuses from before the wipe is read from that backup folder.
"""

import argparse
import base64
import json
import random
import secrets
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Callable, Optional

from fastapi import BackgroundTasks
from sqlalchemy import inspect, select, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

sys.path.insert(0, ".")
from app.core.security import hash_password  # noqa: E402
from app.models.admin import Admin  # noqa: E402
from app.models.admin_access import AdminAccess  # noqa: E402
from app.models.agency_team import AgencyTeam  # noqa: E402
from app.models.common.tenant_registry import Tenant  # noqa: E402
from app.models.pincode import Pincode  # noqa: E402
from app.models.venue import Venue  # noqa: E402
from app.services import user_registry_service  # noqa: E402
# A company with no dropdown lists of its own gets the default company's (services/company_lists).
from app.services.company_lists import LIST_TABLES, copy_lists, has_lists  # noqa: E402,F401
from app.services.training import management  # noqa: E402
from app.utils.date_utils import ist_now  # noqa: E402

BACKUPS = Path("backups")
API_URL = "https://samsung-india-backend.onrender.com"
PHOTO = Path("../assets/bg/trainer_bg.jpg")   # one of the app's own pictures - the server takes JPEG only

# Each company's activity: emptied. Tables a company doesn't have are skipped.
WIPED_TABLES = (
    "assessment", "assessment_results", "attendance", "attendance_logs", "conference_activity_log",
    "conference", "logsmaster", "trainee", "agencyteam",
)
# The ID counters of what is kept (accounts, admins, question sets, bookings, categories,
# subcategories, venues) stay - every other counter goes, so new IDs start again at 10001.
KEPT_COUNTERS = ("ACC", "ADM", "ASM", "BKG", "CAT", "SUB", "VEN")
COMMON_WIPED = ("user_registry",)
COMMON_DROPPED_TABLES = ("login_sessions", "uid_sequence")
REGISTRY_DROPPED_COLUMNS = ("user_type", "created_at", "updated_at")
REGISTRY_DROPPED_CHECK = "ck_user_registry_user_type"

DEVICE_NAME = "Sample data script"
TRAINERS, TRAINEES_BY_FORM, TRAINEES_SELF = 2, 6, 4
PRESENT_PER_TRAINING = 5

# One person each - unique first names, so no two usernames clash in user_registry.
PEOPLE = [
    ("Aarav", "Sharma", "Male"), ("Ananya", "Iyer", "Female"), ("Vivaan", "Reddy", "Male"), ("Diya", "Nair", "Female"),
    ("Aditya", "Patel", "Male"), ("Saanvi", "Gupta", "Female"), ("Arjun", "Singh", "Male"), ("Kavya", "Mehta", "Female"),
    ("Rohan", "Joshi", "Male"), ("Ishita", "Rao", "Female"), ("Karan", "Das", "Male"), ("Meera", "Verma", "Female"),
    ("Nikhil", "Kulkarni", "Male"), ("Pooja", "Menon", "Female"), ("Sai", "Krishnan", "Male"), ("Riya", "Bose", "Female"),
    ("Ishaan", "Chopra", "Male"), ("Neha", "Pillai", "Female"), ("Reyansh", "Malhotra", "Male"), ("Sneha", "Kapoor", "Female"),
    ("Vihaan", "Agarwal", "Male"), ("Priya", "Saxena", "Female"), ("Krishna", "Bhat", "Male"), ("Aadhya", "Jain", "Female"),
]
TRAINER_DESIGNATIONS = ("Senior Trainer", "Trainer")
TRAINEE_DESIGNATIONS = ("Sales Associate", "Customer Advisor", "Retail Executive", "Promoter", "Store Manager")
SUPERVISORS = (("SUP-001", "Rakesh Kumar", "Area Manager"), ("SUP-002", "Sunita Rao", "Zonal Manager"))
# Used when a company's master list offers none (some pickers list only what earlier trainings used).
FALLBACK_OPTIONS = {
    "requestedBy": "Admin", "trainingHub": "Classroom", "audience": "Retail Sales Executives",
    "sessionType": "Classroom Training", "trainingType": "Product Training",
}

OpenSession = Callable[[], Session]


# --- what is there --------------------------------------------------------------------------------


def _tables(conn: Connection) -> list[str]:
    return sorted(inspect(conn).get_table_names())


def table_counts(engine: Engine) -> dict[str, int]:
    with engine.connect() as conn:
        return {t: conn.execute(text(f"SELECT COUNT(*) FROM {_quoted(conn, t)}")).scalar() for t in _tables(conn)}


def _quoted(conn: Connection, name: str) -> str:
    return conn.dialect.identifier_preparer.quote(name)


def print_plan(engines: dict[str, Engine]) -> None:
    """What --apply would delete and keep, table by table - names and counts only."""
    for label, engine in engines.items():
        counts = table_counts(engine)
        if label == "common":
            wiped = {t: n for t, n in counts.items() if t in COMMON_WIPED}
            dropped = {t: n for t, n in counts.items() if t in COMMON_DROPPED_TABLES}
        else:
            wiped = {t: n for t, n in counts.items() if t in WIPED_TABLES}
            dropped = {}
        kept = {t: n for t, n in counts.items() if t not in wiped and t not in dropped and n}
        if label != "common" and "uid_sequence" in counts:
            with engine.connect() as conn:
                gone, stay = _counters(conn, kept=False), _counters(conn, kept=True)
            wiped["uid_sequence (counters " + ", ".join(gone) + ")"] = len(gone)
            kept.pop("uid_sequence", None)
            if stay:
                kept["uid_sequence (counters " + ", ".join(stay) + ")"] = len(stay)
        print(f"\n{label}:")
        print("  delete:  " + (", ".join(f"{t}={n}" for t, n in wiped.items()) or "-"))
        if dropped:
            print("  drop:    " + ", ".join(f"{t} (table, {n} rows)" for t, n in dropped.items()))
        if label == "common":
            print("  drop:    user_registry columns " + ", ".join(REGISTRY_DROPPED_COLUMNS))
        print("  keep:    " + (", ".join(f"{t}={n}" for t, n in kept.items()) or "-"))


def print_sample_preview(common_db: Session, open_tenant: Callable[[str], Session], found: list["Company"]) -> None:
    """What the sample of each company would use from its kept setup - read only."""
    from app.services import catalog_service
    from app.services.assessment_builder_service import list_assessment_suites

    print("\nsample would use:")
    for company in found:
        lists_from = found[0] if company is not found[0] and not _session_has_lists(open_tenant, company.tenant_uid) else company
        if lists_from is not company:
            print(f"  {company.tenant_uid}: has no dropdown lists - gets {lists_from.tenant_uid}'s copied first")
        db, list_db = open_tenant(company.tenant_uid), open_tenant(lists_from.tenant_uid)
        try:
            zones = catalog_service.list_zones(list_db)
            suites = sorted(list_assessment_suites(db, "standardTest"), key=lambda s: -s.noOfQuestion)
            venues = db.query(Venue).filter(Venue.state.isnot(None), Venue.district.isnot(None)).count()
        finally:
            db.close()
            list_db.close()
        try:
            approved_by = approver(common_db, company.tenant_uid).username
        except SystemExit as refusal:
            approved_by = str(refusal)
        suite = f"{suites[0].assessmentSuiteUid} '{suites[0].name}' ({suites[0].noOfQuestion} questions)" if suites else "none - no test"
        print(f"  {company.tenant_uid}: zones {', '.join(z.name for z in zones) or 'none (trainee IDs start TRN)'}; "
              f"test {suite}; venues with a place {venues}; approvals by {approved_by}")


def _session_has_lists(open_tenant: Callable[[str], Session], tenant_uid: str) -> bool:
    db = open_tenant(tenant_uid)
    try:
        return has_lists(db.get_bind())
    finally:
        db.close()


def _counters(conn: Connection, *, kept: bool) -> list[str]:
    prefixes = conn.execute(text("SELECT prefix FROM uid_sequence ORDER BY prefix")).scalars().all()
    return [p for p in prefixes if (p in KEPT_COUNTERS) == kept]


# --- backup and restore ---------------------------------------------------------------------------


def _jsonable(value):
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, timedelta):
        return str(value)
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return {"__b64__": base64.b64encode(value).decode()}
    raise TypeError(f"can't back up a {type(value).__name__}")


def _from_json(value):
    return base64.b64decode(value["__b64__"]) if isinstance(value, dict) and "__b64__" in value else value


def _create_sql(conn: Connection, table: str) -> str:
    if conn.dialect.name == "mysql":
        return conn.execute(text(f"SHOW CREATE TABLE {_quoted(conn, table)}")).first()[1]
    return conn.execute(text("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = :t"), {"t": table}).scalar()


def back_up(engines: dict[str, Engine], folder: Path) -> None:
    """Every table of every database - its definition and its rows - to <folder>/<label>/<table>.json.
    Holds personal data and password hashes: the folder stays on this computer (git ignores backups/)."""
    for label, engine in engines.items():
        target = folder / label
        target.mkdir(parents=True, exist_ok=True)
        with engine.connect() as conn:
            for table in _tables(conn):
                result = conn.execute(text(f"SELECT * FROM {_quoted(conn, table)}"))
                columns = list(result.keys())
                payload = {"table": table, "create": _create_sql(conn, table), "columns": columns,
                           "rows": [list(row) for row in result]}
                (target / f"{table}.json").write_text(json.dumps(payload, default=_jsonable), encoding="utf-8")


def _touched(label: str) -> tuple[str, ...]:
    return COMMON_WIPED + COMMON_DROPPED_TABLES if label == "common" else WIPED_TABLES + LIST_TABLES + ("uid_sequence",)


def restore(engines: dict[str, Engine], folder: Path) -> dict[str, int]:
    """Puts back, from a `back_up` folder, every table the reset changed - as it was: recreated from
    its saved definition, then refilled. Returns the rows restored per database."""
    restored = {}
    for label, engine in engines.items():
        restored[label] = 0
        with engine.begin() as conn:
            mysql = conn.dialect.name == "mysql"
            if mysql:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            for table in _touched(label):
                path = folder / label / f"{table}.json"
                if not path.exists():
                    continue
                saved = json.loads(path.read_text(encoding="utf-8"))
                conn.execute(text(f"DROP TABLE IF EXISTS {_quoted(conn, table)}"))
                conn.execute(text(saved["create"]))
                columns = saved["columns"]
                if saved["rows"]:
                    names = ", ".join(_quoted(conn, c) for c in columns)
                    marks = ", ".join(f":c{i}" for i in range(len(columns)))
                    conn.execute(
                        text(f"INSERT INTO {_quoted(conn, table)} ({names}) VALUES ({marks})"),
                        [{f"c{i}": _from_json(v) for i, v in enumerate(row)} for row in saved["rows"]],
                    )
                restored[label] += len(saved["rows"])
            if mysql:
                conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    return restored


# --- the wipe -------------------------------------------------------------------------------------


def wipe_company(engine: Engine) -> dict[str, int]:
    """Empties a company's activity tables and the counters of their IDs, in one transaction."""
    deleted = {}
    with engine.begin() as conn:
        present = set(_tables(conn))
        for table in WIPED_TABLES:
            if table in present:
                deleted[table] = conn.execute(text(f"DELETE FROM {_quoted(conn, table)}")).rowcount
        if "uid_sequence" in present:
            gone = _counters(conn, kept=False)
            for prefix in gone:
                conn.execute(text("DELETE FROM uid_sequence WHERE prefix = :p"), {"p": prefix})
            deleted["uid_sequence"] = len(gone)
    _restart_numbering(engine, [t for t in WIPED_TABLES if t in deleted])
    return deleted


def wipe_common(engine: Engine) -> dict[str, int]:
    """Empties user_registry, drops its old columns and the two old tables."""
    with engine.begin() as conn:
        deleted = {"user_registry": conn.execute(text("DELETE FROM user_registry")).rowcount}
    with engine.begin() as conn:
        columns = {c["name"] for c in inspect(conn).get_columns("user_registry")}
        if conn.dialect.name == "mysql":
            checks = set(conn.execute(text(
                "SELECT CONSTRAINT_NAME FROM information_schema.TABLE_CONSTRAINTS WHERE TABLE_SCHEMA = DATABASE() "
                "AND TABLE_NAME = 'user_registry' AND CONSTRAINT_TYPE = 'CHECK'"
            )).scalars())
            if REGISTRY_DROPPED_CHECK in checks:
                conn.execute(text(f"ALTER TABLE user_registry DROP CHECK {REGISTRY_DROPPED_CHECK}"))
        for column in REGISTRY_DROPPED_COLUMNS:
            if column in columns:
                conn.execute(text(f"ALTER TABLE user_registry DROP COLUMN {column}"))
        for table in COMMON_DROPPED_TABLES:
            conn.execute(text(f"DROP TABLE IF EXISTS {_quoted(conn, table)}"))
    _restart_numbering(engine, list(COMMON_WIPED))
    return deleted


def _restart_numbering(engine: Engine, tables: list[str]) -> None:
    """Row ids of the emptied tables start again at 1 (MySQL; SQLite does it by itself)."""
    if engine.dialect.name != "mysql":
        return
    with engine.begin() as conn:
        for table in tables:
            conn.execute(text(f"ALTER TABLE {_quoted(conn, table)} AUTO_INCREMENT = 1"))


# --- the company as the sample needs it -----------------------------------------------------------


@dataclass
class Company:
    tenant_uid: str
    name: str
    agency_uid: Optional[str]
    number: int                      # 0, 1, ... - keeps each company's phone numbers apart
    company_uid: Optional[str] = None   # what the PHP system puts in agencyteam.companyUid
    options: dict[str, str] = field(default_factory=dict)   # today's form values, for empty pickers

    @property
    def code(self) -> str:
        return self.tenant_uid.strip().upper()


def _backed_up_rows(folder: Path, label: str, table: str) -> list[dict]:
    path = folder / label / f"{table}.json"
    if not path.exists():
        return []
    saved = json.loads(path.read_text(encoding="utf-8"))
    return [dict(zip(saved["columns"], row)) for row in saved["rows"]]


def companies(common_db: Session, open_tenant: Callable[[str], Session], backup: Optional[Path] = None) -> list[Company]:
    """Every active company, the default one first, with the companyUid its trainers carry and the
    values its trainings use, which the sample reuses - read from the databases BEFORE the wipe, or
    after it from the wipe's `backup` folder."""
    from collections import Counter

    from app.core.config import settings

    tenants = common_db.query(Tenant).filter(Tenant.status == "active").order_by(Tenant.id).all()
    tenants.sort(key=lambda t: t.tenant_uid != settings.DEFAULT_TENANT_ID)
    found = []
    for number, tenant in enumerate(tenants):
        company = Company(tenant.tenant_uid, tenant.company_name, tenant.agency_uid, number)
        if backup is not None:
            trainers = _backed_up_rows(backup, tenant.tenant_uid, "agencyteam")
            trainings = _backed_up_rows(backup, tenant.tenant_uid, "conference")
            company.company_uid = next((t.get("companyUid") for t in trainers if t.get("companyUid")), None)
            for column in FALLBACK_OPTIONS:
                used = Counter(t.get(column) for t in trainings if t.get(column))
                company.options[column] = used.most_common(1)[0][0] if used else FALLBACK_OPTIONS[column]
            found.append(company)
            continue
        db = open_tenant(tenant.tenant_uid)
        try:
            company.company_uid = db.execute(
                select(AgencyTeam.companyUid).where(AgencyTeam.companyUid.isnot(None)).limit(1)
            ).scalar()
            present = {c["name"] for c in inspect(db.connection()).get_columns("conference")}
            for column in ("requestedBy", "trainingHub", "audience", "sessionType", "trainingType"):
                if column not in present:
                    company.options[column] = FALLBACK_OPTIONS[column]
                    continue
                value = db.execute(text(
                    f"SELECT {column} FROM conference WHERE {column} IS NOT NULL AND {column} <> '' "
                    f"GROUP BY {column} ORDER BY COUNT(*) DESC LIMIT 1"
                )).scalar()
                company.options[column] = value or FALLBACK_OPTIONS[column]
        finally:
            db.close()
        found.append(company)
    return found


# --- the sample -----------------------------------------------------------------------------------


class ApiError(RuntimeError):
    def __init__(self, what: str, status: int, detail):
        super().__init__(f"{what}: {status} {detail}")
        self.status, self.detail = status, detail

    @property
    def code(self) -> Optional[str]:
        return self.detail.get("code") if isinstance(self.detail, dict) else None


@dataclass
class Person:
    first: str
    last: str
    gender: str

    @property
    def name(self) -> str:
        return f"{self.first} {self.last}"

    @property
    def username(self) -> str:
        return f"{self.first}.{self.last}".lower()

    @property
    def email(self) -> str:
        return f"{self.username}@example.com"


@dataclass
class SeedReport:
    trainers: list[tuple[str, str, str]] = field(default_factory=list)            # (company, ID, username)
    trainees: list[tuple[str, str, Optional[str]]] = field(default_factory=list)  # (company, ID, username or None)
    trainings: list[tuple[str, str, str]] = field(default_factory=list)           # (company, ID, finished / scheduled)


class Seeder:
    """Makes the sample through `api` (the live server - or, in the tests, the app in process) except
    the trainers (the PHP system's job) and the approvals (an admin's), which go to the databases."""

    def __init__(self, api, open_common: OpenSession, open_tenant: Callable[[str], Session], password: str,
                 photo: bytes, clock: Callable[[], datetime] = ist_now, seed: int = 20261020):
        self.api, self.open_common, self.open_tenant = api, open_common, open_tenant
        self.password, self.photo, self.clock = password, photo, clock
        self.rng = random.Random(seed)
        self.people = iter(())
        self.report = SeedReport()

    @staticmethod
    def people_for(company: Company) -> list[Person]:
        """The company's own slice of PEOPLE - the same people whichever companies one run makes."""
        size = TRAINERS + TRAINEES_BY_FORM + TRAINEES_SELF
        return [Person(*p) for p in PEOPLE[company.number * size:(company.number + 1) * size]]

    # -- the HTTP side

    def call(self, method: str, path: str, token: Optional[str] = None, what: str = "", **kwargs):
        headers = dict(kwargs.pop("headers", {}) or {})
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = self.api.request(method, path, headers=headers, **kwargs)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail")
            except ValueError:
                detail = response.text[:200]
            raise ApiError(what or path, response.status_code, detail)
        return response.json() if response.content else None

    def sign_in_staff(self, username: str) -> str:
        body = {"username": username, "password": self.password, "deviceId": f"seed-{username}", "deviceName": DEVICE_NAME}
        return self.call("POST", "/admin/login", json=body, what=f"trainer sign-in {username}")["access_token"]

    def sign_in_trainee(self, username: str) -> str:
        body = {"identifier": username, "password": self.password, "deviceId": f"seed-{username}", "deviceName": DEVICE_NAME}
        return self.call("POST", "/trainees/login", json=body, what=f"trainee sign-in {username}")["access_token"]

    # -- one company

    def seed(self, company: Company) -> None:
        self.people = iter(self.people_for(company))
        trainers = [self.add_trainer(company, n) for n in range(1, TRAINERS + 1)]
        tokens = {t.username: self.sign_in_staff(t.username) for t in trainers}
        lead = tokens[trainers[0].username]
        pick = self.pickers(lead)

        trainees: list[tuple[str, str]] = []   # (ID, token)
        for n in range(TRAINEES_BY_FORM):
            trainer = trainers[n % 2]
            trainees.append(self.add_trainee_by_form(company, n + 1, trainer, tokens[trainer.username], pick))
        for n in range(TRAINEES_SELF):
            trainees.append(self.self_register(company, TRAINEES_BY_FORM + n + 1, pick))

        suite = self.test_suite(lead)
        venues = self.venues(company)
        for n in range(4):
            trainer = trainers[n % 2]
            finished = n < 2
            # A finished one starts now (read afresh: a start more than a minute off the planned time
            # needs a reason); a scheduled one at 10:00 AM next week.
            now = self.clock().replace(second=0, microsecond=0)
            start = now if finished else datetime.combine(now.date() + timedelta(days=7 + n), time(10, 0))
            uid = self.add_training(company, trainer, tokens[trainer.username], pick, suite, venues[n % len(venues)] if venues else None,
                                    start)
            self.approve(company, uid)
            if finished:
                group = trainees[(n * PRESENT_PER_TRAINING) % len(trainees):][:PRESENT_PER_TRAINING]
                self.run_training(uid, tokens[trainer.username], group, suite)
            self.report.trainings.append((company.tenant_uid, uid, "finished" if finished else "scheduled"))

    def add_trainer(self, company: Company, n: int) -> AgencyTeam:
        """As the PHP system adds one - then into user_registry, as the sync would."""
        person = next(self.people)
        common_db, db = self.open_common(), self.open_tenant(company.tenant_uid)
        try:
            state, district, pincode = self.place(common_db)
            trainer = AgencyTeam(
                agencyTeamUid=user_registry_service.claim_trainer_uid(common_db, db),
                companyUid=company.company_uid, company=company.name, name=person.name, email=person.email,
                phone=self.phone(company, 90 + n), gender=person.gender, offerId=f"{company.code}-OFF-{n:03d}",
                designation=TRAINER_DESIGNATIONS[(n - 1) % len(TRAINER_DESIGNATIONS)], role="trainer",
                jobCity=district, jobState=state, jobPincode=pincode, username=person.username,
                password=hash_password(self.password), status="Approved", tokenVersion=0,
            )
            # A column the PHP system's table requires gets that table's own default when the sample
            # leaves it empty (Samsung's profilePhoto: 'defaultfile.png' - its "no photo").
            for column, default in _required_defaults(db, "agencyteam").items():
                if getattr(trainer, column, "") is None:
                    setattr(trainer, column, default)
            db.add(trainer)
            db.commit()
            db.refresh(trainer)
            user_registry_service.sync_account(common_db, company.tenant_uid, trainer)
            self.report.trainers.append((company.tenant_uid, trainer.agencyTeamUid, trainer.username))
            db.expunge(trainer)
            return trainer
        finally:
            db.close()
            common_db.close()

    def place(self, common_db: Session) -> tuple[str, str, Optional[str]]:
        rows = common_db.query(Pincode.stateName, Pincode.district, Pincode.pincode).order_by(Pincode.id).all()
        if not rows:
            return "Delhi", "New Delhi", None
        state, district, pincode = rows[self.rng.randrange(len(rows))]
        return state, district, str(pincode) if pincode else None

    def phone(self, company: Company, n: int) -> int:
        return 9_100_000_000 + company.number * 1_000_000 + n

    def pickers(self, token: str) -> dict:
        """What the forms' pickers offer, asked the way the forms ask."""
        zones = [z for z in self.call("GET", "/admin/zones", token, what="zones") if z["options"]]
        states = [s for s in self.call("GET", "/admin/states", token, what="states") if s["options"]]
        trainers = {o["value"]: o.get("name") or o["label"] for o in self.call("GET", "/admin/trainers", token, what="trainers")}
        lists = {key: [o["value"] for o in self.call("GET", path, token, what=key)] for key, path in (
            ("requestedBy", "/admin/requested-by-options"), ("trainingHub", "/admin/training-hubs"),
            ("audience", "/admin/audiences"), ("sessionType", "/admin/session-types"), ("trainingType", "/admin/training-types"),
        )}
        return {"zones": zones, "states": states, "trainers": trainers, "lists": lists}

    def option(self, company: Company, pick: dict, key: str) -> str:
        offered = pick["lists"][key]
        return offered[0] if offered else company.options[key]

    def zone_region(self, pick: dict, n: int) -> tuple[Optional[str], Optional[str]]:
        if not pick["zones"]:
            return None, None
        zone = pick["zones"][n % len(pick["zones"])]
        return zone["name"], zone["options"][n % len(zone["options"])]

    def state_district(self, pick: dict, n: int) -> tuple[str, Optional[str]]:
        if not pick["states"]:
            return "Delhi", None
        state = pick["states"][(n * 7) % len(pick["states"])]
        return state["name"], state["options"][n % len(state["options"])]

    def add_trainee_by_form(self, company: Company, n: int, trainer: AgencyTeam, token: str, pick: dict) -> tuple[str, str]:
        person = next(self.people)
        zone, region = self.zone_region(pick, n)
        state, district = self.state_district(pick, n)
        supervisor = SUPERVISORS[n % len(SUPERVISORS)]
        body = {
            "agencyId": company.agency_uid, "fullName": person.name, "designation": TRAINEE_DESIGNATIONS[n % len(TRAINEE_DESIGNATIONS)],
            "gender": person.gender, "dob": date(1994 + n % 6, 1 + n % 12, 3 + n).isoformat(),
            "primaryEmail": person.email, "primaryPhone": str(self.phone(company, n)),
            "address": f"{10 + n}, MG Road, {district or state}", "state": state, "district": district,
            "zone": zone or "", "region": region or "", "requestedBy": self.option(company, pick, "requestedBy"),
            "trainerId": trainer.username, "trainerName": pick["trainers"].get(trainer.username, trainer.name),
            "supervisorId": supervisor[0], "supervisorName": supervisor[1], "supervisorDesignation": supervisor[2],
            "joinedOn": date(2025, 1 + n % 12, 1).isoformat(), "jobStatus": "Active", "jobCity": district,
            "username": person.username, "password": self.password,
        }
        made = self.call("POST", "/admin/trainees", token, json=body, what=f"add trainee {person.username}")
        self.report.trainees.append((company.tenant_uid, made["traineeUid"], person.username))
        return made["traineeUid"], self.sign_in_trainee(person.username)

    def self_register(self, company: Company, n: int, pick: dict) -> tuple[str, str]:
        person = next(self.people)
        zone, region = self.zone_region(pick, n)
        state, district = self.state_district(pick, n)
        body = {
            "name": person.name, "phone": self.phone(company, n), "email": person.email, "gender": person.gender,
            "designation": TRAINEE_DESIGNATIONS[n % len(TRAINEE_DESIGNATIONS)], "employee_id": f"{company.code}-EMP-{n:03d}",
            "supervisorName": SUPERVISORS[n % len(SUPERVISORS)][1], "state": state, "district": district,
            "zone": zone, "region": region, "deviceId": f"seed-{person.username}", "deviceName": DEVICE_NAME,
        }
        made = self.call("POST", "/trainees/register", json=body, headers={"X-Tenant-ID": company.tenant_uid},
                         what=f"self sign-up {person.username}")
        self.report.trainees.append((company.tenant_uid, made["trainee"]["traineeUid"], None))
        return made["trainee"]["traineeUid"], made["access_token"]

    def test_suite(self, token: str) -> Optional[dict]:
        suites = self.call("GET", "/admin/assessment-suites", token, params={"module": "standardTest"}, what="question sets")
        usable = [s for s in suites if s["noOfQuestion"] >= 1]
        return max(usable, key=lambda s: s["noOfQuestion"]) if usable else None

    def venues(self, company: Company) -> list[Venue]:
        db = self.open_tenant(company.tenant_uid)
        try:
            venues = db.query(Venue).filter(Venue.state.isnot(None), Venue.district.isnot(None)).order_by(Venue.id).all()
            for venue in venues:
                db.expunge(venue)
            return venues
        finally:
            db.close()

    @staticmethod
    def windows(start: datetime) -> tuple[str, dict, dict]:
        """The training's start time and its attendance / test windows, as the form's time pickers
        write them ("02:30 PM"): check-in from 5 minutes before the start for 30 minutes, then the
        test for 30 - kept inside the training's day (the form compares times within one day)."""
        day_start, day_end = datetime.combine(start.date(), time(0, 0)), datetime.combine(start.date(), time(23, 59))
        opens = max(start - timedelta(minutes=5), day_start)
        attendance_end = min(start + timedelta(minutes=30), max(start, day_end - timedelta(minutes=1)))
        test_end = min(attendance_end + timedelta(minutes=30), day_end)
        clock = lambda moment: moment.strftime("%I:%M %p")
        return clock(start), {"checkInOpens": clock(opens), "checkOutCloses": clock(attendance_end), "geoFencing": False}, {
            "startTime": clock(attendance_end), "endTime": clock(test_end)}

    def add_training(self, company: Company, trainer: AgencyTeam, token: str, pick: dict, suite: Optional[dict],
                     venue: Optional[Venue], start: datetime) -> str:
        starts, attendance, test_window = self.windows(start)
        day = start.date()
        zone, region = (venue.zone, venue.region) if venue and venue.zone else self.zone_region(pick, day.day)
        state, district = (venue.state, venue.district) if venue else self.state_district(pick, day.day)
        flow = {"attendance": attendance}
        if suite:
            flow["standardTest"] = {
                "category": suite["category"], "assessmentSuiteUid": suite["assessmentSuiteUid"],
                "questionCount": min(5, suite["noOfQuestion"]), **test_window, "checkIn": True, "unlockCondition": "Automatic",
            }
        body = {
            "zone": zone, "region": region, "requestedBy": self.option(company, pick, "requestedBy"),
            "trainerEmployeeId": trainer.username, "trainerName": pick["trainers"].get(trainer.username, trainer.name),
            "state": state, "district": district, "venue": venue.venueUid if venue else None, "isResidential": False,
            "conferenceDate": day.isoformat(), "conferenceTime": starts, "trainingHub": self.option(company, pick, "trainingHub"),
            "audience": self.option(company, pick, "audience"), "sessionType": self.option(company, pick, "sessionType"),
            "trainingType": self.option(company, pick, "trainingType"), "batchSize": "25", "sessionFlow": flow, "checklist": [],
        }
        return self.call("POST", "/admin/trainings", token, json=body, what="add training")["conferenceUid"]

    def approve(self, company: Company, conference_uid: str) -> None:
        """What the company admin's Approve button runs - the one step that needs an admin."""
        common_db, db = self.open_common(), self.open_tenant(company.tenant_uid)
        try:
            admin = approver(common_db, company.tenant_uid)
            management.approve_training(db, admin, conference_uid, background_tasks=BackgroundTasks(),
                                        common_db=common_db, tenant_id=company.tenant_uid)
        finally:
            db.close()
            common_db.close()

    def run_training(self, uid: str, token: str, trainees: list[tuple[str, str]], suite: Optional[dict]) -> None:
        photo = ("photo.jpg", self.photo, "image/jpeg")
        base = f"/admin/trainings/{uid}"
        try:
            self.call("POST", f"{base}/start", token, files={"photo": photo}, what=f"start {uid}")
        except ApiError as exc:
            if exc.code != "SCHEDULE_OVERRIDE":
                raise
            # Started off its planned minute: the app asks the trainer why, and so do we.
            self.call("POST", f"{base}/start", token, files={"photo": photo},
                      data={"scheduleOverrideReason": "Started a few minutes late"}, what=f"start {uid}")
        self.call("POST", f"{base}/modules/ATTENDANCE/start", token, what=f"open check-in {uid}")
        code = self.call("GET", f"{base}/join-code", token, what=f"QR code {uid}")["joinCode"]
        for trainee_uid, trainee_token in trainees:
            self.call("POST", f"/sessions/join/{code}", trainee_token, what=f"{trainee_uid} joins {uid}")
            self.call("POST", "/attendance/check-in", trainee_token, json={"conferenceUid": uid}, what=f"{trainee_uid} checks in")
        if suite:
            self.call("POST", f"{base}/advance-module", token, what=f"open the test {uid}")
            suite_uid = suite["assessmentSuiteUid"]
            for trainee_uid, trainee_token in trainees:
                questions = self.call("GET", f"/assessments/{suite_uid}/questions", trainee_token,
                                      params={"conferenceUid": uid}, what=f"{trainee_uid} reads the test")["questions"]
                answers = [{"questionId": q["id"], "selectedOption": self.rng.choice(q["options"])["id"] if q["options"] else None}
                           for q in questions]
                self.call("POST", f"/assessments/{suite_uid}/submit", trainee_token, json={"conferenceUid": uid, "answers": answers},
                          what=f"{trainee_uid} submits the test")
        self.call("POST", f"{base}/modules/stop-active", token, what=f"close {uid}'s module")
        self.call("POST", f"{base}/end", token, files={"photo": photo, "attendanceSheet": ("attendance.jpg", self.photo, "image/jpeg")},
                  data={"totalPax": str(len(trainees))}, what=f"end {uid}")


def _required_defaults(db: Session, table: str) -> dict[str, str]:
    """The NOT NULL columns of a MySQL table that have a plain default, with it ({} elsewhere)."""
    if db.get_bind().dialect.name != "mysql":
        return {}
    rows = db.execute(text(
        "SELECT COLUMN_NAME, COLUMN_DEFAULT FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() "
        "AND TABLE_NAME = :t AND IS_NULLABLE = 'NO' AND COLUMN_DEFAULT IS NOT NULL AND EXTRA = ''"), {"t": table}).all()
    return {column: default for column, default in rows if default.upper() != "CURRENT_TIMESTAMP"}


def approver(common_db: Session, tenant_uid: str) -> Admin:
    """The company's own company admin, else a Super Admin - whose Approve the sample's trainings get."""
    from app.services.access_service import AccessRole

    for role in (AccessRole.COMPANY_ADMIN, AccessRole.SUPER_ADMIN):
        grant = (common_db.query(AdminAccess)
                 .filter(AdminAccess.role == role, AdminAccess.active == 1,
                         (AdminAccess.tenant_uid == tenant_uid) | AdminAccess.tenant_uid.is_(None))
                 .order_by(AdminAccess.tenant_uid.is_(None), AdminAccess.id).first())
        admin = common_db.get(Admin, grant.admin_id) if grant else None
        if admin is not None and admin.role == "admin":
            return admin
    raise SystemExit(f"Refused: {tenant_uid} has no company admin or Super Admin to approve the sample trainings.")


def write_accounts(folder: Path, password: str, report: SeedReport, name: str = "sample-accounts.txt") -> Path:
    lines = ["Sample accounts made by scripts/reset_and_seed.py - one password for all that have one.",
             f"Password: {password}", "", "Trainers (staff sign-in):"]
    lines += [f"  {company:10} {uid:14} {username}" for company, uid, username in report.trainers]
    lines += ["", "Trainees (trainee sign-in; self sign-ups have no password - they were signed in once, at sign-up):"]
    lines += [f"  {company:10} {uid:14} {username or '(self sign-up, no password)'}" for company, uid, username in report.trainees]
    path = folder / name
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# --- running it -----------------------------------------------------------------------------------


def _engines() -> dict[str, Engine]:
    from app.database.common import common_engine
    from scripts._tenant_db import tenant_engine

    engines = {"common": common_engine}
    with common_engine.connect() as conn:
        for (tenant_uid,) in conn.execute(text("SELECT tenant_uid FROM tenants WHERE status = 'active' ORDER BY id")):
            engines[tenant_uid] = tenant_engine(tenant_uid)
    return engines


def main() -> None:
    parser = argparse.ArgumentParser(description="Wipe activity data and make sample data (dry run unless --apply).")
    parser.add_argument("--apply", action="store_true", help="back up, wipe and make the sample (default: dry run)")
    parser.add_argument("--restore", type=Path, help="put back the tables a reset changed, from its backup folder")
    parser.add_argument("--seed-only", type=Path, metavar="BACKUP",
                        help="only make the sample, after a wipe whose backup folder this is (refused unless the activity is empty)")
    parser.add_argument("--company", help="with --seed-only: make only this company's sample (its tenant ID)")
    parser.add_argument("--api", default=API_URL, help=f"the server to make the sample through (default {API_URL})")
    args = parser.parse_args()
    if args.company and not args.seed_only:
        parser.error("--company goes with --seed-only")

    import httpx
    from sqlalchemy.orm import sessionmaker

    from app.database.common import CommonSessionLocal

    engines = _engines()
    try:
        if args.restore:
            print("restored rows:", restore(engines, args.restore))
            return
        if not args.seed_only:
            print_plan(engines)
        sessions = {uid: sessionmaker(bind=engine) for uid, engine in engines.items() if uid != "common"}
        reading = CommonSessionLocal()
        try:
            found = companies(reading, lambda uid: sessions[uid](), backup=args.seed_only)
            if not args.seed_only:
                print_sample_preview(reading, lambda uid: sessions[uid](), found)
        finally:
            reading.close()
        if not (args.apply or args.seed_only):
            print("\ndry run - nothing was written. Run again with --apply.")
            return
        default_company = found[0]
        if args.company:
            found = [c for c in found if c.tenant_uid == args.company]
            if not found:
                raise SystemExit(f"Refused: no active company '{args.company}'.")
        if args.seed_only:
            left = {c.tenant_uid: {t: n for t, n in table_counts(engines[c.tenant_uid]).items() if n and t in WIPED_TABLES}
                    for c in found}
            with engines["common"].connect() as conn:
                for c in found:
                    registered = conn.execute(text("SELECT COUNT(*) FROM user_registry WHERE tenant_uid = :t"), {"t": c.tenant_uid}).scalar()
                    if registered:
                        left[c.tenant_uid]["user_registry"] = registered
            if any(left.values()):
                raise SystemExit(f"Refused: the activity isn't empty - {left}. --seed-only is for after a wipe.")

        # Refused before anything is touched: more companies than sample people, or a server that
        # doesn't answer (a sleeping one wakes up here, not half way through the sample).
        if len(found) * (TRAINERS + TRAINEES_BY_FORM + TRAINEES_SELF) > len(PEOPLE):
            raise SystemExit(f"Refused: {len(found)} companies need more sample people than the {len(PEOPLE)} listed.")
        if httpx.get(args.api.rstrip("/") + "/", timeout=180).status_code != 200:
            raise SystemExit(f"Refused: {args.api} isn't answering - nothing was changed.")

        if args.seed_only:
            folder = args.seed_only
        else:
            folder = BACKUPS / f"reset-{datetime.now():%Y%m%d-%H%M%S}"
            back_up(engines, folder)
            print(f"\nbacked up to {folder}")
            for uid in sessions:
                print(f"wiped {uid}: {wipe_company(engines[uid])}")
            print(f"wiped common: {wipe_common(engines['common'])}")
        for company in found:
            if company is default_company:
                continue
            copied = copy_lists(engines[default_company.tenant_uid], engines[company.tenant_uid])
            if copied:
                print(f"copied {default_company.tenant_uid}'s dropdown lists into {company.tenant_uid}: {copied}")

        password = secrets.token_urlsafe(12)
        with httpx.Client(base_url=args.api, timeout=120) as api:
            seeder = Seeder(api, CommonSessionLocal, lambda uid: sessions[uid](), password, PHOTO.read_bytes())
            try:
                for company in found:
                    seeder.seed(company)
                    print(f"made {company.tenant_uid}'s sample")
            finally:
                # A one-company run keeps its own file - the earlier run's accounts stay as they were.
                name = f"sample-accounts-{args.company}.txt" if args.company else "sample-accounts.txt"
                accounts = write_accounts(folder, password, seeder.report, name)
                print(f"sample accounts (usernames and the password): {accounts}")
        print("\nafter:")
        for label, engine in engines.items():
            print(f"  {label}: " + ", ".join(f"{t}={n}" for t, n in table_counts(engine).items() if n))
        print(f"\nTo undo: venv/Scripts/python.exe scripts/reset_and_seed.py --restore {folder}")
    finally:
        for label, engine in engines.items():
            if label != "common":
                engine.dispose()


if __name__ == "__main__":
    main()

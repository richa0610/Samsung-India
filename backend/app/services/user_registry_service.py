"""The central user registry (user, 2026-10-19): one row per trainee and trainer of every company in
the shared Common Database (models/common/user_registry.py), so a person can sign in with only their
username and password and the server still knows their company.

Registering someone touches two databases no single transaction covers, so it runs in this order:
  1. take the person's ID from their company's own counter - first raised past every ID the registry
     holds, so it never repeats another company's - and reserve a `pending` registry row. Its unique
     columns refuse a username, HO ID or ID another account holds, even when two registrations race:
     an ID another company took at the same moment is given up for the next one;
  2. save the company record (and the counter claim with it);
  3. read it back, then mark the registry row `active`.
A failure in 2 releases the reservation. A crash between 2 and 3 leaves a `pending` row that
`reconcile_tenant` settles: record there -> active, else removed. Accounts changed outside this app
(the PHP system writes `agencyteam` directly) are brought in by `reconcile_tenant` too."""

import logging
from dataclasses import dataclass, field
from itertools import chain
from typing import Callable, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.database.tenant import tenant_manager
from app.models import uid_events
from app.models.agency_team import AgencyTeam
from app.models.common.user_registry import UserRegistry
from app.models.trainee import Trainee
from app.models.uid_sequence import UidSequence
from app.repositories import tenant_repository, trainee_repository
from app.repositories import user_registry_repository as registry
from app.repositories.user_registry_repository import login_key
from app.services.access_service import norm
from app.utils import uid as uid_utils

logger = logging.getLogger("user_registry")

USERNAME_TAKEN = "This username is already used by another account"
HOID_TAKEN = "This HO ID is already registered to another account"
ALREADY_REGISTERED = "This account is already registered"
UNAVAILABLE = "Registration is temporarily unavailable. Please try again."
NOT_READY = (
    "The trainee was saved, but their sign-in isn't ready yet - it completes on its own within a few "
    "minutes. Don't register them again."
)
# The start of a `remarks` the sync writes when it disables a row - the only disabled rows a later
# sync may enable again (one an admin disabled stays disabled).
SYNC_REMARK = "sync: "
# How many IDs a registration tries when other companies keep taking the one it claimed meanwhile.
ID_ATTEMPTS = 3

OpenTenant = Callable[[str], Session]


@dataclass(frozen=True)
class Account:
    """The registry's view of one company record. `user_type` is the table it came from - read, never
    stored."""

    user_type: str
    user_uid: Optional[str]
    username: Optional[str]
    hoid: Optional[str]
    phone: Optional[int]
    password_hash: Optional[str]
    may_sign_in: bool


def _trainee_account(uid, username, hoid, phone, password) -> Account:
    return Account("trainee", uid, login_key(username), login_key(hoid), phone, password or None, True)


def _trainer_account(uid, username, hoid, phone, password, role) -> Account:
    # Only an agency account with the trainer role signs in (the approved rule, access_service).
    return Account("trainer", uid, login_key(username), login_key(hoid), phone, password or None, norm(role) == "trainer")


def account_of(record: Trainee | AgencyTeam) -> Account:
    if isinstance(record, Trainee):
        return _trainee_account(record.traineeUid, record.username, record.employee_id, record.phone, record.password)
    return _trainer_account(record.agencyTeamUid, record.username, record.offerId, record.phone, record.password, record.role)


def _open_tenant(common_db: Session) -> OpenTenant:
    return lambda tenant_uid: tenant_manager.get_session(tenant_uid, common_db)


# --- registration -----------------------------------------------------------------------------------


def ensure_available(common_db: Session, *, username=None, hoid=None, exclude_user_uid: Optional[str] = None) -> None:
    """Refuses (400) a username or HO ID another account already holds, in any company."""
    if registry.holder(common_db, "username", username, exclude_user_uid):
        raise bad_request(USERNAME_TAKEN)
    if registry.holder(common_db, "hoid", hoid, exclude_user_uid):
        raise bad_request(HOID_TAKEN)


def claim_trainee_uid(common_db: Session, db: Session, zone) -> str:
    """The next trainee ID for a trainee of `db`'s company, inside `db`'s transaction - committed with
    the company record, rolled back with it (`first_unused_number` says where it starts)."""
    prefix = uid_events.trainee_uid_prefix(zone)
    uid_utils.raise_counter_floor(db.connection(), prefix, first_unused_number(common_db, db, prefix, Trainee.traineeUid))
    return uid_events.new_trainee_uid(db.connection(), zone)


def claim_trainer_uid(common_db: Session, db: Session) -> str:
    """The next trainer ID (AGT...) for `db`'s company, inside `db`'s transaction. This app never
    creates trainers (the PHP system does); a maintenance script uses this to give a company's trainers
    IDs no other company has (scripts/reissue_people_ids.py)."""
    prefix = uid_events.TRAINER_UID_PREFIX
    uid_utils.raise_counter_floor(db.connection(), prefix, first_unused_number(common_db, db, prefix, AgencyTeam.agencyTeamUid))
    return uid_events.next_uid(db.connection(), prefix)


def first_unused_number(common_db: Session, db: Session, prefix: str, column=Trainee.traineeUid) -> int:
    """The first number for `prefix` that neither the registry (every company's people) nor `db`'s
    company has used: past that company's own counter and every ID in `column` (a trainee's, or a
    trainer's) it carries - one the sync hasn't brought into the registry yet included."""
    counter = db.execute(select(UidSequence.next_val).where(UidSequence.prefix == prefix)).scalar()
    own = db.execute(select(column).where(column.like(f"{prefix}%"))).scalars()
    registered = common_db.execute(select(UserRegistry.user_uid).where(UserRegistry.user_uid.like(f"{prefix}%"))).scalars()
    serials = [serial for serial in (uid_utils.serial_of(uid, prefix) for uid in chain(own, registered)) if serial is not None]
    return max(uid_utils.START, counter or uid_utils.START, max(serials, default=0) + 1)


def _reserve(common_db: Session, tenant_uid: str, account: Account) -> Optional[UserRegistry]:
    """Commits a `pending` row. The unique columns refuse what another account took meanwhile: an ID
    -> None (the caller claims the next); a username or HO ID -> a 400 naming it. Nothing is kept."""
    entry = UserRegistry(
        tenant_uid=tenant_uid, user_uid=account.user_uid, username=account.username,
        hoid=account.hoid, phone=account.phone, password_hash=account.password_hash, status="pending",
    )
    common_db.add(entry)
    try:
        common_db.commit()
    except IntegrityError:
        common_db.rollback()
        if registry.get_by_uid(common_db, account.user_uid) is not None:
            return None
        ensure_available(common_db, username=account.username, hoid=account.hoid)
        raise bad_request(ALREADY_REGISTERED)
    return entry


def _activate(common_db: Session, entry: UserRegistry) -> None:
    entry.status = "active"
    common_db.commit()


def _release(common_db: Session, entry: UserRegistry) -> None:
    """Drops the reservation of a registration that failed. If even that fails, a sync removes the
    stale `pending` row later."""
    try:
        common_db.delete(entry)
        common_db.commit()
    except SQLAlchemyError:
        common_db.rollback()
        logger.exception("Couldn't release registry reservation %s - the sync will", entry.user_uid)


def register_trainee(
    common_db: Session, db: Session, tenant_uid: str, trainee: Trainee, *, username_is_id: bool = False
) -> Trainee:
    """Saves a new trainee in their company's database and in the registry, in the order the module
    docstring gives; the trainee comes back saved. `username_is_id`: a trainee registered without a
    username signs in with the ID the app made."""
    ensure_available(common_db, username=trainee.username, hoid=trainee.employee_id)
    username_is_id = username_is_id and not trainee.username
    try:
        for _attempt in range(ID_ATTEMPTS):
            trainee.traineeUid = claim_trainee_uid(common_db, db, trainee.zone)
            if username_is_id:
                trainee.username = trainee.traineeUid
            entry = _reserve(common_db, tenant_uid, account_of(trainee))
            if entry is not None:
                break
            db.rollback()   # gives the claimed number back; the next claim starts past the taken ID
        else:
            logger.error("Registry kept refusing new '%s' IDs - registration refused", trainee.traineeUid)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE)
    except Exception:
        db.rollback()
        raise

    try:
        trainee = trainee_repository.create(db, trainee)
    except Exception:
        db.rollback()
        _release(common_db, entry)
        raise
    # Not done until the company record reads back.
    if trainee_repository.get_by_uid(db, trainee.traineeUid) is None:
        _release(common_db, entry)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE)
    try:
        _activate(common_db, entry)
    except SQLAlchemyError:
        common_db.rollback()
        logger.exception("Registry entry %s left pending - the sync will activate it", trainee.traineeUid)
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=NOT_READY)
    return trainee


# --- changes made in this app ------------------------------------------------------------------------


def sync_account(common_db: Session, tenant_uid: Optional[str], record: Trainee | AgencyTeam) -> None:
    """Copies a company record this app just changed (phone, HO ID, password) into its registry row,
    adding the row for an account registered before the registry. Best effort - the company record is
    already saved: a failure is logged and the sync repairs it. A new HO ID is checked with
    `ensure_available` before the company record is saved."""
    account = account_of(record)
    if not account.user_uid:
        return
    try:
        entry = registry.get_by_uid(common_db, account.user_uid)
        if entry is None:
            if not tenant_uid:
                return
            entry = UserRegistry(tenant_uid=tenant_uid, user_uid=account.user_uid)
            common_db.add(entry)
        elif entry.tenant_uid != tenant_uid:
            logger.warning("Registry row %s belongs to tenant '%s', not '%s' - left alone", account.user_uid, entry.tenant_uid, tenant_uid)
            return
        entry.username, entry.hoid, entry.phone, entry.password_hash = account.username, account.hoid, account.phone, account.password_hash
        if entry.status in (None, "pending"):
            entry.status = "active" if account.may_sign_in else "disabled"
        common_db.commit()
    except SQLAlchemyError:
        common_db.rollback()
        logger.exception("Couldn't update registry row %s - the sync will", account.user_uid)


# --- the sync ----------------------------------------------------------------------------------------


@dataclass
class ReconcileReport:
    tenant_uid: str
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    disabled: int = 0
    removed: int = 0
    # (company record ID, why) - IDs and field names only, nothing personal.
    skipped: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class KnownEntries:
    """The registry as a sync sees it: read once, then kept in step with what the sync adds - so one
    run over several companies, a dry run included, sees the clashes between them."""

    rows: list[UserRegistry]
    by_uid: dict[str, UserRegistry]
    holders: dict[str, dict[str, UserRegistry]]


def known_entries(common_db: Session) -> KnownEntries:
    rows = registry.list_all(common_db)
    return KnownEntries(
        rows=rows,
        by_uid={row.user_uid.lower(): row for row in rows},
        holders={attr: {getattr(row, attr): row for row in rows if getattr(row, attr)} for attr in ("username", "hoid")},
    )


def _company_accounts(tenant_db: Session) -> list[Account]:
    trainees = tenant_db.execute(
        select(Trainee.traineeUid, Trainee.username, Trainee.employee_id, Trainee.phone, Trainee.password)
    ).all()
    trainers = tenant_db.execute(
        select(AgencyTeam.agencyTeamUid, AgencyTeam.username, AgencyTeam.offerId, AgencyTeam.phone, AgencyTeam.password, AgencyTeam.role)
    ).all()
    return [_trainee_account(*row) for row in trainees] + [_trainer_account(*row) for row in trainers]


def _apply(entry: UserRegistry, account: Account, holders: dict, report: ReconcileReport) -> bool:
    """Makes `entry` match `account`; True when anything changed. A username / HO ID another entry
    holds is left out (and reported) - the person still signs in with their other identifiers."""
    changed = False

    def put(attr, value):
        nonlocal changed
        if getattr(entry, attr) != value:
            setattr(entry, attr, value)
            changed = True

    for attr in ("username", "hoid"):
        value = getattr(account, attr)
        owner = holders[attr].get(value) if value else None
        if owner is not None and owner is not entry:
            report.skipped.append((account.user_uid, f"{attr} already used by {owner.user_uid}"))
            value = None
        old = getattr(entry, attr)
        if old and old != value and holders[attr].get(old) is entry:
            del holders[attr][old]
        if value:
            holders[attr][value] = entry
        put(attr, value)
    put("phone", account.phone)
    put("password_hash", account.password_hash)

    wanted = "active" if account.may_sign_in else "disabled"
    if entry.status in (None, "pending") or (entry.status == "active" and wanted == "disabled"):
        put("status", wanted)
        put("remarks", None if wanted == "active" else f"{SYNC_REMARK}not a trainer role")
    elif entry.status == "disabled" and wanted == "active" and (entry.remarks or "").startswith(SYNC_REMARK):
        put("status", "active")
        put("remarks", None)
    return changed


def reconcile_tenant(
    common_db: Session, tenant_db: Session, tenant_uid: str, *, apply: bool = True, known: Optional[KnownEntries] = None
) -> ReconcileReport:
    """Brings the registry in line with one company's database: adds the accounts it lacks (the PHP
    system's, ones made before the registry), copies changed usernames / HO IDs / phones / password
    hashes, activates finished registrations, disables rows whose account is gone or isn't a trainer
    (a row an admin disabled is left alone) and removes reservations whose registration never finished.
    An ID another company's row holds is skipped and reported. apply=False writes nothing (a dry run).

    `known`: shared by a run over several companies, so each sees what the ones before it added. A dry
    run sharing it is rolled back by its caller after the last company - nothing is flushed meanwhile
    (sessions here don't autoflush), so nothing reaches the database."""
    report = ReconcileReport(tenant_uid)
    shared = known is not None
    known = known or known_entries(common_db)
    rows, by_uid, holders = known.rows, known.by_uid, known.holders
    seen: set[str] = set()

    for account in _company_accounts(tenant_db):
        if not account.user_uid:
            report.skipped.append(("-", f"a {account.user_type} with no ID"))
            continue
        key = account.user_uid.lower()
        if key in seen:
            report.skipped.append((account.user_uid, "ID used twice in this company"))
            continue
        seen.add(key)
        entry = by_uid.get(key)
        if entry is not None and entry.tenant_uid != tenant_uid:
            report.skipped.append((account.user_uid, f"ID already registered to company {entry.tenant_uid}"))
            continue
        if entry is None:
            entry = UserRegistry(tenant_uid=tenant_uid, user_uid=account.user_uid)
            _apply(entry, account, holders, report)
            common_db.add(entry)
            by_uid[key] = entry
            rows.append(entry)
            report.added += 1
        elif _apply(entry, account, holders, report):
            report.updated += 1
        else:
            report.unchanged += 1

    for entry in list(rows):
        if entry.tenant_uid != tenant_uid or entry.user_uid.lower() in seen:
            continue
        if entry.status == "pending":
            # No company record: a registration that failed. One still saving it at this very moment
            # finds its reservation gone - it answers NOT_READY, and the next sync adds the row back.
            common_db.delete(entry)
            rows.remove(entry)
            by_uid.pop(entry.user_uid.lower(), None)
            report.removed += 1
        elif entry.status == "active":
            entry.status = "disabled"
            entry.remarks = f"{SYNC_REMARK}no longer in the company database"
            report.disabled += 1

    if apply:
        common_db.commit()
    elif not shared:
        common_db.rollback()
    return report


def reconcile_all(common_db: Session, open_tenant: Optional[OpenTenant] = None) -> list[ReconcileReport]:
    """`reconcile_tenant` for every active company, each in its own session, closed after. One company
    that can't be read is logged and skipped - the others still sync."""
    open_tenant = open_tenant or _open_tenant(common_db)
    reports = []
    for tenant_uid in tenant_repository.list_active_uids(common_db):
        try:
            tenant_db = open_tenant(tenant_uid)
        except HTTPException:
            logger.exception("Registry sync skipped tenant '%s'", tenant_uid)
            continue
        try:
            reports.append(reconcile_tenant(common_db, tenant_db, tenant_uid))
        except SQLAlchemyError:
            common_db.rollback()
            logger.exception("Registry sync failed for tenant '%s'", tenant_uid)
        finally:
            tenant_db.close()
    return reports

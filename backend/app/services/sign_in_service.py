"""Sign-in without a company code (user, 2026-10-19). The person types their username, HO ID, ID or
phone and password; the central user registry (services/user_registry_service) says which company
they belong to, and their record in that company's database - the source of truth - decides.

Every check a sign-in with a company code makes is made here too, against the company the registry
names (never one a client sent): the company is active, the account exists there and still answers
to what was typed, the password matches its CURRENT hash (a registry copy that went stale - the PHP
system changed it - is refreshed first), a trainer still has the trainer role, and the account isn't
locked by failed sign-ins. The failure counts are the ones the company-code sign-in keeps
(trainee_service.lock_key, admin_service), so switching between the two buys no extra guesses.

Admin-table accounts aren't in the registry: their companies come from their admin_access grants -
one signs them straight in, several answer 409 CHOOSE_COMPANY with the list and a 2-minute ticket for
`choose_company`. The ticket is signed with its own key, so it can never pass for a sign-in token."""

import functools
import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import func, or_
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core import rate_limit
from app.core.config import settings
from app.core.exceptions import conflict, forbidden, unauthorized
from app.core.security import hash_password, is_token_current, verify_password
from app.core.ttl_cache import TTLCache
from app.database.tenant import tenant_manager
from app.models import uid_events
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.models.common.user_registry import UserRegistry
from app.models.trainee import Trainee
from app.repositories import admin_repository, tenant_repository
from app.repositories import user_registry_repository as registry
from app.repositories.user_registry_repository import login_key
from app.schemas.admin import AdminAuthSession
from app.schemas.trainee import TokenResponse
from app.services import admin_service, tenant_directory, trainee_service, user_registry_service
from app.services.access_service import granted_tenants, resolve_scope
from app.services.device_sessions import Device

logger = logging.getLogger("sign_in")

SHARED_PHONE = "This phone number is used by more than one account. Please log in with your HO ID or username."
CHOOSE_COMPANY = "Choose the company to sign in to"
TICKET_EXPIRED = "That sign-in has expired. Please sign in again."
TICKET_MINUTES = 2
# The unknown IDs a sign-in looked for in every company and didn't find - not looked for again for a
# minute, so a burst of made-up IDs doesn't read every company's database each time.
_not_found = TTLCache(ttl_seconds=60, max_entries=10_000)


@functools.lru_cache(maxsize=1)
def _dummy_hash() -> str:
    """A bcrypt hash nobody's password matches - checked when no account was found, so that answer
    takes as long as a wrong password."""
    return hash_password(secrets.token_urlsafe(24))


@dataclass
class _Verified:
    entry: UserRegistry
    record: Trainee | AgencyTeam
    db: Session   # the record's company session, still open - whoever holds this closes it


# --- finding and checking the account ----------------------------------------------------------------


def _record(db: Session, entry: UserRegistry) -> Trainee | AgencyTeam | None:
    if entry.user_type == "trainee":
        return db.query(Trainee).filter(Trainee.traineeUid == entry.user_uid).first()
    return db.query(AgencyTeam).filter(AgencyTeam.agencyTeamUid == entry.user_uid).first()


def _answers_to(account: user_registry_service.Account, key: str) -> bool:
    """Whether what was typed still names this account in its company record."""
    return key in {account.username, account.hoid, (account.user_uid or "").lower(), str(account.phone) if account.phone else None}


def _lock(entry: UserRegistry, record: Trainee | AgencyTeam) -> tuple[str, str]:
    """The failure count the company-code sign-in keeps for this account."""
    if entry.user_type == "trainee":
        return trainee_service.LOGIN_SCOPE, trainee_service.lock_key(entry.tenant_uid, record)
    return admin_service.LOGIN_SCOPE, f"{entry.tenant_uid}:{record.username}"


def _disable(common_db: Session, entry: UserRegistry, reason: str) -> None:
    try:
        entry.status = "disabled"
        entry.remarks = f"{user_registry_service.SYNC_REMARK}{reason}"
        common_db.commit()
    except SQLAlchemyError:
        common_db.rollback()
        logger.exception("Couldn't disable registry row %s", entry.user_uid)


def _check(common_db: Session, entry: UserRegistry, key: str, password: str) -> Optional[_Verified]:
    """The account behind `entry` if it signs in with `password`, else None. Raises 429 for a locked
    account and 503 when its company's database can't be reached."""
    if entry.status != "active":
        return None
    if entry.user_type == "trainee" and uid_events.is_trainer_uid(entry.user_uid):
        return None   # a trainer-shaped ID never signs in as a trainee (uid_events.TRAINER_UID_PREFIX)
    try:
        db = tenant_manager.get_session(entry.tenant_uid, common_db)
    except HTTPException as exc:
        if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            raise
        return None   # a suspended or unknown company
    verified = None
    try:
        record = _record(db, entry)
        if record is None:
            _disable(common_db, entry, "no longer in the company database")
            return None
        account = user_registry_service.account_of(record)
        if not _answers_to(account, key) or account.password_hash != entry.password_hash:
            # Changed in the company (the PHP system writes there directly): refresh the copy first.
            user_registry_service.sync_account(common_db, entry.tenant_uid, record)
            if not _answers_to(account, key):
                return None
        scope, lock = _lock(entry, record)
        rate_limit.ensure_account_not_locked(scope, lock)
        if not (account.password_hash and verify_password(password, account.password_hash)):
            rate_limit.record_account_failure(scope, lock)
            return None
        rate_limit.clear_account_failures(scope, lock)
        verified = _Verified(entry, record, db)
        return verified
    finally:
        if verified is None:
            db.close()


def _matching_records(db: Session, key: str, user_type: str) -> list[Trainee | AgencyTeam]:
    model, uid, hoid = (Trainee, Trainee.traineeUid, Trainee.employee_id) if user_type == "trainee" else (
        AgencyTeam, AgencyTeam.agencyTeamUid, AgencyTeam.offerId)
    conditions = [func.lower(uid) == key, func.lower(model.username) == key, func.lower(hoid) == key]
    if key.isascii() and key.isdigit() and len(key) <= 15:
        conditions.append(model.phone == int(key))
    return db.query(model).filter(or_(*conditions)).all()


def _discover(common_db: Session, key: str, user_type: str) -> None:
    """For an ID the registry doesn't know: looks for it in every active company and registers what it
    finds, so an account created outside this app (the PHP system's) signs in at once."""
    if _not_found.get((user_type, key)):
        return
    found = False
    for tenant_uid in tenant_repository.list_active_uids(common_db):
        try:
            db = tenant_manager.get_session(tenant_uid, common_db)
        except HTTPException:
            logger.warning("Sign-in couldn't look in tenant '%s'", tenant_uid)
            continue
        try:
            for record in _matching_records(db, key, user_type):
                user_registry_service.sync_account(common_db, tenant_uid, record)
                found = True
        finally:
            db.close()
    if not found:
        _not_found.set((user_type, key), True)


def _sign_in(common_db: Session, typed: str, password: str, user_type: str, scope: str, failed: str) -> _Verified:
    """The one account `typed` + `password` sign in to, or the refusal: 401 `failed` (the same words
    whatever went wrong), 409 SHARED_PHONE when the password opens more than one account sharing that
    phone, 429 for a locked account."""
    key = login_key(typed)
    candidates = registry.find_for_login(common_db, key, user_type)
    if key and not candidates:
        _discover(common_db, key, user_type)
        candidates = registry.find_for_login(common_db, key, user_type)
    if not candidates:
        typed_lock = f"*:typed-{key}"
        rate_limit.ensure_account_not_locked(scope, typed_lock)
        verify_password(password, _dummy_hash())
        rate_limit.record_account_failure(scope, typed_lock)
        raise unauthorized(failed)

    verified: list[_Verified] = []
    try:
        for entry in candidates:
            match = _check(common_db, entry, key, password)
            if match is not None:
                verified.append(match)
    except Exception:
        for match in verified:
            match.db.close()
        raise
    if len(verified) == 1:
        return verified[0]
    for match in verified:
        match.db.close()
    if verified:
        raise conflict(SHARED_PHONE)
    raise unauthorized(failed)


# --- the sign-ins ------------------------------------------------------------------------------------


def sign_in_trainee(
    common_db: Session, identifier: str, password: str, ip_address: Optional[str] = None, device: Optional[Device] = None
) -> TokenResponse:
    found = _sign_in(common_db, identifier, password, "trainee", trainee_service.LOGIN_SCOPE, trainee_service.LOGIN_FAILED)
    try:
        session = trainee_service.signed_in(
            found.db, found.record, found.entry.tenant_uid, ip_address, common_db=common_db, device=device
        )
    finally:
        found.db.close()
    session.company = tenant_directory.describe(common_db, found.entry.tenant_uid)
    return session


def sign_in_staff(
    common_db: Session, username: str, password: str, ip_address: Optional[str] = None, device: Optional[Device] = None
) -> AdminAuthSession:
    """An admin-table account first, as with a company code (admin_service.login), then a trainer."""
    admin_lock = f"*:{username}"
    rate_limit.ensure_account_not_locked(admin_service.LOGIN_SCOPE, admin_lock)
    admin = admin_repository.get_admin_by_username(common_db, username)
    if admin and admin.password and verify_password(password, admin.password):
        rate_limit.clear_account_failures(admin_service.LOGIN_SCOPE, admin_lock)
        tenants = granted_tenants(common_db, admin)
        if not tenants:
            raise forbidden(admin_service.NOT_AUTHORIZED)
        if len(tenants) == 1:
            return _admin_signed_in(common_db, admin, tenants[0], ip_address)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "CHOOSE_COMPANY",
                "message": CHOOSE_COMPANY,
                "companies": [tenant_directory.describe(common_db, tenant).model_dump() for tenant in tenants],
                "ticket": _ticket(admin, tenants),
            },
        )

    try:
        found = _sign_in(common_db, username, password, "trainer", admin_service.LOGIN_SCOPE, admin_service.LOGIN_FAILED)
    except HTTPException as exc:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            rate_limit.record_account_failure(admin_service.LOGIN_SCOPE, admin_lock)
        raise
    try:
        # Only an agency account with the trainer role signs in as a trainer (the approved rule).
        if not resolve_scope(common_db, found.record, found.entry.tenant_uid).is_trainer:
            raise forbidden(admin_service.NOT_AUTHORIZED)
        session = admin_service.trainer_signed_in(
            found.db, found.record, found.entry.tenant_uid, ip_address, common_db=common_db, device=device
        )
    finally:
        found.db.close()
    session.company = tenant_directory.describe(common_db, found.entry.tenant_uid)
    return session


def _admin_signed_in(common_db: Session, admin: Admin, tenant_id: str, ip_address: Optional[str]) -> AdminAuthSession:
    db = tenant_manager.get_session(tenant_id, common_db)
    try:
        session = admin_service.admin_signed_in(db, admin, tenant_id, ip_address)
    finally:
        db.close()
    session.company = tenant_directory.describe(common_db, tenant_id)
    return session


# --- the company choice of an admin with several -----------------------------------------------------


def _ticket_key() -> str:
    # Never the sign-in tokens' key, so a ticket can't pass for one (nor one for a ticket).
    return f"{settings.SECRET_KEY}|company-choice"


def _ticket(admin: Admin, tenants: list[str]) -> str:
    issued = datetime.now(timezone.utc)
    claims = {
        "sub": admin.username, "purpose": "company-choice", "companies": tenants, "ver": int(admin.tokenVersion or 0),
        "iat": issued, "exp": issued + timedelta(minutes=TICKET_MINUTES),
    }
    return jwt.encode(claims, _ticket_key(), algorithm=settings.ALGORITHM)


def choose_company(common_db: Session, ticket: str, tenant_id: str, ip_address: Optional[str] = None) -> AdminAuthSession:
    """Signs in the admin a `sign_in_staff` ticket names to one of the companies it listed - each
    re-checked now: the account, its token version, and its grant for that company."""
    try:
        claims = jwt.decode(ticket, _ticket_key(), algorithms=[settings.ALGORITHM])
    except JWTError:
        raise unauthorized(TICKET_EXPIRED)
    if claims.get("purpose") != "company-choice":
        raise unauthorized(TICKET_EXPIRED)
    if tenant_id not in (claims.get("companies") or []):
        raise forbidden(admin_service.NOT_AUTHORIZED)
    admin = admin_repository.get_admin_by_username(common_db, claims.get("sub") or "")
    if admin is None or not is_token_current(claims, admin):
        raise unauthorized(TICKET_EXPIRED)
    if not resolve_scope(common_db, admin, tenant_id).allowed:
        raise forbidden(admin_service.NOT_AUTHORIZED)
    return _admin_signed_in(common_db, admin, tenant_id, ip_address)

"""The central user registry - `user_registry`, in the shared (Common) database."""

from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.common.user_registry import UserRegistry


def login_key(value) -> Optional[str]:
    """How a username or HO ID is stored and matched: spaces around it ignored, any letter case.
    None for a blank one - it names nobody, and never counts as a duplicate."""
    key = str(value).strip().lower() if value is not None else ""
    return key or None


def get_by_uid(common_db: Session, user_uid: Optional[str]) -> Optional[UserRegistry]:
    """The entry for a company record's ID - in SQL lower case, so it matches the same on every collation."""
    if not user_uid:
        return None
    return common_db.query(UserRegistry).filter(func.lower(UserRegistry.user_uid) == user_uid.strip().lower()).first()


def holder(common_db: Session, field: str, value, exclude_user_uid: Optional[str] = None) -> Optional[UserRegistry]:
    """The entry that holds this username / HO ID (`field`), other than `exclude_user_uid`'s own."""
    key = login_key(value)
    if key is None:
        return None
    query = common_db.query(UserRegistry).filter(getattr(UserRegistry, field) == key)
    if exclude_user_uid:
        query = query.filter(func.lower(UserRegistry.user_uid) != exclude_user_uid.strip().lower())
    return query.first()


def find_for_login(common_db: Session, key: Optional[str]) -> list[UserRegistry]:
    """Every entry a sign-in's typed `key` (already `login_key`'d) names: by username, HO ID or ID, or
    - all digits - by phone; trainees and trainers alike (their company record says which). More than
    one only for a phone two people share."""
    if not key:
        return []
    conditions = [UserRegistry.username == key, UserRegistry.hoid == key, func.lower(UserRegistry.user_uid) == key]
    if key.isascii() and key.isdigit() and len(key) <= 15:   # fits the BIGINT column
        conditions.append(UserRegistry.phone == int(key))
    return common_db.query(UserRegistry).filter(or_(*conditions)).all()


def list_all(common_db: Session) -> list[UserRegistry]:
    """Every entry - the registry has one row per person, so a reconcile holds it in memory."""
    return common_db.query(UserRegistry).all()

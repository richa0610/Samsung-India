"""The tenant registry - `tenants`, in the shared (Common) database."""

from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.common.tenant_registry import Tenant


def code_key(code: Optional[str]) -> str:
    """How a typed or sent tenant ID is matched: spaces around it ignored, any letter case
    ("SAMSUNG " and "samsung" are one tenant)."""
    return (code or "").strip().lower()


def get(common_db: Session, tenant_uid: str) -> Optional[Tenant]:
    """The tenant registered under exactly this ID (as a verified token or the server names it)."""
    return common_db.query(Tenant).filter(Tenant.tenant_uid == tenant_uid).first()


def find_by_code(common_db: Session, code: Optional[str]) -> Optional[Tenant]:
    """The tenant a person typed or an app sent, matched by `code_key` - in SQL lower case, so it
    behaves the same on every database collation."""
    wanted = code_key(code)
    if not wanted:
        return None
    return common_db.query(Tenant).filter(func.lower(Tenant.tenant_uid) == wanted).first()


def list_uids(common_db: Session) -> list[str]:
    """Every registered tenant ID - the registry holds one row per client company, so it is small."""
    return [uid for (uid,) in common_db.query(Tenant.tenant_uid)]

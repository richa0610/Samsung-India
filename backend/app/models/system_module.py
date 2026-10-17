from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database.connection import CommonBase


class SystemModule(CommonBase):
    """Mirrors the `system_modules` table from mmtbtwob_tops — the permission
    module registry. Each row represents a named feature/section of the system
    that can be individually granted or denied via `user_permissions`.

    No ORM relationship to `UserPermission` here (unlike the original
    single-database version): `system_modules` now lives in the shared
    Common Database while `user_permissions` lives in each tenant's own
    database as part of the DB-per-tenant split, and a relationship/FK
    can't span two separate physical databases. See user_permission.py."""

    __tablename__ = "system_modules"

    id = Column(Integer, primary_key=True, index=True)
    module_key = Column(String(50), unique=True)
    module_name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

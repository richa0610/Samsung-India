from sqlalchemy import Column, Enum, Integer, text

from app.database.connection import Base


class UserPermission(Base):
    """Mirrors the `user_permissions` table from mmtbtwob_tops — module-level
    read/write access control per user. Each row grants (or denies) one module
    to one user.

    `module_id` points at `system_modules.id`, but is a plain column (no FK
    constraint, no ORM relationship) rather than a real foreign key: this
    table lives in each tenant's own database while `system_modules` moved
    to the shared Common Database as part of the DB-per-tenant split, and a
    real FK/relationship can't span two separate physical databases."""

    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)

    # Points to the `id` of the row in the table named by `table_type`
    user_id = Column(Integer)
    table_type = Column(
        Enum("admin", "agencyteam", "trainee", name="user_permissions_table_type")
    )
    module_id = Column(Integer, index=True)

    can_read = Column(Integer, server_default=text("0"))
    can_write = Column(Integer, server_default=text("0"))

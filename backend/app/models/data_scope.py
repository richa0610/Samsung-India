from sqlalchemy import Column, Enum, Integer, String

from app.database.connection import Base


class DataScope(Base):
    """Mirrors the `data_scopes` table from mmtbtwob_tops — RBAC data-scoping
    rules that restrict what rows a user can see. A user (admin, agencyteam,
    or trainee) may have multiple scope rows (e.g. zone='North' AND
    state='Delhi')."""

    __tablename__ = "data_scopes"

    id = Column(Integer, primary_key=True, index=True)

    # Points to the `id` of the row in the table named by `table_type`
    user_id = Column(Integer, index=True)
    table_type = Column(
        Enum("admin", "agencyteam", "trainee", name="data_scopes_table_type")
    )
    scope_type = Column(
        Enum("zone", "state", "region", "district", "trainer_id",
             name="data_scopes_scope_type")
    )
    scope_value = Column(String(100))

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

logger = logging.getLogger("schema_sync")


def sync_missing_columns(engine: Engine, base) -> None:
    """Best-effort, additive-only schema sync for a stack with no migration
    framework (`create_all()` is the only schema mechanism this app has, and
    it only creates missing TABLES - it never alters an existing one). So a
    column added to a model after its table already exists in the live
    database - e.g. Tenant.live_proctoring_enabled, added after `tenants`
    already existed on Aiven - silently never appears there, and any query
    selecting it 1054s ("Unknown column").

    Adds any column present on a mapped model but missing from the live
    table, using the column's own `server_default` (if any) so existing rows
    get a sane value. Never drops, renames, or alters an existing column -
    safe to run on every startup; each column is independent, so one
    failure (e.g. a permissions issue) doesn't block the rest."""
    inspector = inspect(engine)
    for table in base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue  # create_all() already creates a brand-new table in full
        existing = {c["name"] for c in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing:
                continue
            ddl = f"ALTER TABLE {table.name} ADD COLUMN {column.name} {column.type.compile(engine.dialect)}"
            if column.server_default is not None:
                ddl += f" DEFAULT {column.server_default.arg}"
            if not column.nullable:
                ddl += " NOT NULL"
            try:
                with engine.begin() as conn:
                    conn.execute(text(ddl))
                logger.warning("Schema sync: added missing column %s.%s", table.name, column.name)
            except Exception as exc:
                logger.error("Schema sync: failed to add %s.%s: %s", table.name, column.name, exc)


def sync_missing_indexes(engine: Engine, base) -> None:
    """Same idea as sync_missing_columns, for indexes: `create_all()` never adds
    an index to a table that already exists, so an `Index(...)` declared on a
    model after the table went live would silently never appear. Creates any
    named index the model declares that the live table lacks. Additive only and
    per-index best-effort (a failure is logged, never raised)."""
    inspector = inspect(engine)
    for table in base.metadata.sorted_tables:
        if not inspector.has_table(table.name):
            continue
        existing = {ix["name"] for ix in inspector.get_indexes(table.name)}
        for index in table.indexes:
            if not index.name or index.name in existing:
                continue
            try:
                index.create(bind=engine)
                logger.warning("Schema sync: created index %s on %s", index.name, table.name)
            except Exception as exc:
                logger.error("Schema sync: failed to create index %s: %s", index.name, exc)

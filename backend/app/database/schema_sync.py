import logging

from sqlalchemy import Column, inspect, text
from sqlalchemy.engine import Dialect, Engine

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
            if column.name not in existing:
                _add_column(engine, table.name, column)


def add_column_ddl(table_name: str, column: Column, dialect: Dialect) -> str:
    """The ALTER TABLE that adds `column` as its model declares it: its type, its own
    server_default (so existing rows get a sane value) and NOT NULL when it isn't nullable."""
    ddl = f"ALTER TABLE {table_name} ADD COLUMN {column.name} {column.type.compile(dialect)}"
    if column.server_default is not None:
        ddl += f" DEFAULT {column.server_default.arg}"
    if not column.nullable:
        ddl += " NOT NULL"
    return ddl


def _add_column(engine: Engine, table_name: str, column: Column) -> None:
    """Adds one missing column. A failure to run it is logged, never raised, so it can't block the rest."""
    ddl = add_column_ddl(table_name, column, engine.dialect)
    try:
        with engine.begin() as conn:
            conn.execute(text(ddl))
        logger.warning("Schema sync: added missing column %s.%s", table_name, column.name)
    except Exception:
        logger.exception("Schema sync: failed to add %s.%s", table_name, column.name)


def relax_columns(engine: Engine, table_name: str, wanted: dict[str, tuple[bool, str | None]]) -> list[str]:
    """Loosens existing MySQL columns to `wanted` - {column: (may be NULL, DEFAULT clause or None)} -
    for a model that relaxed a column after its table went live (create_all and the column sync never
    alter one). Only ever loosens: a NOT NULL column may become NULL, a column without a default gets
    one; each keeps its live type and collation. A column already as wanted is left alone, so this is
    safe on every startup; one failure is logged and the rest still run. Returns what it changed."""
    if engine.dialect.name != "mysql":
        return []
    changed = []
    with engine.connect() as conn:
        live = {row.COLUMN_NAME: row for row in conn.execute(text(
            "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLLATION_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = :t"), {"t": table_name})}
    for column, (nullable, default) in wanted.items():
        row = live.get(column)
        if row is None:
            continue
        needs_null = nullable and row.IS_NULLABLE == "NO"
        needs_default = default is not None and row.COLUMN_DEFAULT is None
        if not (needs_null or needs_default):
            continue
        ddl = f"ALTER TABLE {table_name} MODIFY {column} {row.COLUMN_TYPE}"
        if row.COLLATION_NAME:
            ddl += f" COLLATE {row.COLLATION_NAME}"
        ddl += " NULL" if nullable or row.IS_NULLABLE == "YES" else " NOT NULL"
        if default is not None:
            ddl += f" DEFAULT {default}"
        try:
            with engine.begin() as conn:
                conn.execute(text(ddl))
            changed.append(column)
            logger.warning("Schema sync: relaxed %s.%s", table_name, column)
        except Exception:
            logger.exception("Schema sync: failed to relax %s.%s", table_name, column)
    return changed


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
            except Exception:
                logger.exception("Schema sync: failed to create index %s", index.name)

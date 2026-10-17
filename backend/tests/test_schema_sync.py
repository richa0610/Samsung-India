"""schema_sync adds columns a model declares but the live table lacks - the only way a new column
reaches a running database on this stack (it runs against production on every startup)."""

import unittest

from sqlalchemy import Column, Integer, String, create_engine, inspect, text
from sqlalchemy.dialects import mysql
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import StaticPool

from app.database.schema_sync import add_column_ddl, sync_missing_columns

Base = declarative_base()


class Thing(Base):
    __tablename__ = "thing"
    id = Column(Integer, primary_key=True)
    flag = Column(Integer, nullable=False, server_default=text("1"))
    note = Column(String(50))
    status = Column(String(20), server_default=text("'Pending'"))
    required = Column(String(20), nullable=False)   # no default: an existing table can't take it


class AddColumnDdl(unittest.TestCase):
    def ddl(self, column_name):
        return add_column_ddl("thing", Thing.__table__.c[column_name], mysql.dialect())

    def test_the_type_default_and_not_null_come_from_the_model(self):
        self.assertEqual(self.ddl("flag"), "ALTER TABLE thing ADD COLUMN flag INTEGER DEFAULT 1 NOT NULL")
        self.assertEqual(self.ddl("note"), "ALTER TABLE thing ADD COLUMN note VARCHAR(50)")
        self.assertEqual(self.ddl("status"), "ALTER TABLE thing ADD COLUMN status VARCHAR(20) DEFAULT 'Pending'")


class SyncMissingColumns(unittest.TestCase):
    def test_missing_columns_are_added_and_one_failure_does_not_block_the_rest(self):
        engine = create_engine("sqlite://", poolclass=StaticPool)
        self.addCleanup(engine.dispose)
        with engine.begin() as conn:
            conn.execute(text("CREATE TABLE thing (id INTEGER PRIMARY KEY)"))
            conn.execute(text("INSERT INTO thing (id) VALUES (1)"))

        with self.assertLogs("schema_sync", level="WARNING") as logs:
            sync_missing_columns(engine, Base)

        columns = {c["name"] for c in inspect(engine).get_columns("thing")}
        self.assertEqual(columns, {"id", "flag", "note", "status"})   # `required` was refused, the rest still added
        self.assertTrue(any("failed to add thing.required" in line for line in logs.output))
        with engine.connect() as conn:
            self.assertEqual(conn.execute(text("SELECT flag, status FROM thing")).one(), (1, "Pending"))


if __name__ == "__main__":
    unittest.main()

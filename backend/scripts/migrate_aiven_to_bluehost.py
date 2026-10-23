import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

import pymysql
from app.core.secret_box import encrypt_secret

AIVEN_CONFIG = {
    "host": os.environ.get("SOURCE_DB_HOST", "mysql-1987f2a9-richa-61ad.l.aivencloud.com"),
    "port": int(os.environ.get("SOURCE_DB_PORT", 15866)),
    "user": os.environ.get("SOURCE_DB_USER", "avnadmin"),
    "password": os.environ.get("SOURCE_DB_PASSWORD", ""),
    "connect_timeout": 15,
}

BLUEHOST_CONFIG = {
    "host": os.environ.get("TARGET_DB_HOST", "129.121.73.181"),
    "port": int(os.environ.get("TARGET_DB_PORT", 3306)),
    "user": os.environ.get("TARGET_DB_USER", "mmtbtwob_richa"),
    "password": os.environ.get("TARGET_DB_PASSWORD", ""),
    "connect_timeout": 15,
}

MAPPING = [
    ("tops_common_db", "mmtbtwob_tops_common"),
    ("tops_samsung_db", "mmtbtwob_tops_samsung"),
    ("tops_demo", "mmtbtwob_tops_demo"),
]

BATCH_SIZE = 250


def migrate_database(src_db: str, dst_db: str) -> dict[str, tuple[int, int]]:
    print(f"\n=======================================================")
    print(f"Migrating: {src_db}  ==>  {dst_db}")
    print(f"=======================================================")

    src_conn = pymysql.connect(**AIVEN_CONFIG, database=src_db)
    dst_conn = pymysql.connect(**BLUEHOST_CONFIG, database=dst_db)

    results = {}

    try:
        with src_conn.cursor() as src_cur:
            src_cur.execute("SET SESSION sql_mode = 'ANSI_QUOTES,NO_AUTO_VALUE_ON_ZERO';")

        with dst_conn.cursor() as dst_cur:
            dst_cur.execute("SET FOREIGN_KEY_CHECKS = 0;")
            dst_cur.execute("SET SESSION sql_mode = 'ANSI_QUOTES,NO_AUTO_VALUE_ON_ZERO';")

        with src_conn.cursor() as src_cur:
            src_cur.execute("SHOW TABLES;")
            tables = [r[0] for r in src_cur.fetchall()]

        print(f"Found {len(tables)} tables in {src_db}.")

        for table in tables:
            # 1. Get Table DDL from Aiven
            with src_conn.cursor() as src_cur:
                src_cur.execute(f"SHOW CREATE TABLE `{table}`;")
                create_stmt = src_cur.fetchone()[1]

            # 2. Create Table on Bluehost
            with dst_conn.cursor() as dst_cur:
                dst_cur.execute(f"DROP TABLE IF EXISTS `{table}`;")
                dst_cur.execute(create_stmt)
            dst_conn.commit()

            # 3. Read Columns and Data from Aiven
            with src_conn.cursor() as src_cur:
                src_cur.execute(f"SELECT * FROM `{table}`;")
                rows = src_cur.fetchall()
                col_names = [desc[0] for desc in src_cur.description]

            src_count = len(rows)

            # 4. Insert rows into Bluehost in batches
            if src_count > 0:
                placeholders = ", ".join(["%s"] * len(col_names))
                quoted_cols = ", ".join([f"`{c}`" for c in col_names])
                insert_sql = f"INSERT INTO `{table}` ({quoted_cols}) VALUES ({placeholders});"

                with dst_conn.cursor() as dst_cur:
                    for i in range(0, src_count, BATCH_SIZE):
                        batch = rows[i : i + BATCH_SIZE]
                        dst_cur.executemany(insert_sql, batch)
                dst_conn.commit()

            # 5. Verify row count
            with dst_conn.cursor() as dst_cur:
                dst_cur.execute(f"SELECT COUNT(*) FROM `{table}`;")
                dst_count = dst_cur.fetchone()[0]

            results[table] = (src_count, dst_count)
            match_str = "OK" if src_count == dst_count else "MISMATCH!"
            print(f"  [{match_str}] Table: {table:<28} | Source: {src_count:>5} rows | Target: {dst_count:>5} rows")

        with dst_conn.cursor() as dst_cur:
            dst_cur.execute("SET FOREIGN_KEY_CHECKS = 1;")
        dst_conn.commit()

    finally:
        src_conn.close()
        dst_conn.close()

    return results


def update_tenants_registry() -> None:
    print(f"\n=======================================================")
    print("Updating Bluehost Common Database `tenants` registry...")
    print("=======================================================")

    dst_conn = pymysql.connect(**BLUEHOST_CONFIG, database="mmtbtwob_tops_common")
    try:
        encrypted_pw = encrypt_secret(BLUEHOST_CONFIG["password"])

        updates = [
            ("samsung", "mmtbtwob_tops_samsung"),
            ("demo", "mmtbtwob_tops_demo"),
        ]

        with dst_conn.cursor() as cur:
            for tenant_uid, db_name in updates:
                cur.execute(
                    """
                    UPDATE tenants
                    SET database_host = %s,
                        database_port = %s,
                        database_username = %s,
                        database_name = %s,
                        database_password = %s
                    WHERE tenant_uid = %s;
                    """,
                    (
                        BLUEHOST_CONFIG["host"],
                        BLUEHOST_CONFIG["port"],
                        BLUEHOST_CONFIG["user"],
                        db_name,
                        encrypted_pw,
                        tenant_uid,
                    ),
                )
                print(f"  + Configured Tenant '{tenant_uid}' -> DB: '{db_name}' on {BLUEHOST_CONFIG['host']}:{BLUEHOST_CONFIG['port']}")

        dst_conn.commit()
    finally:
        dst_conn.close()


def run_full_migration() -> None:
    all_summary = {}

    for src_db, dst_db in MAPPING:
        res = migrate_database(src_db, dst_db)
        all_summary[dst_db] = res

    update_tenants_registry()

    print("\n=======================================================")
    print("            MIGRATION COMPLETE SUMMARY                 ")
    print("=======================================================")
    total_tables = 0
    total_rows = 0
    all_matched = True

    for dst_db, tables in all_summary.items():
        print(f"\nDatabase: {dst_db} ({len(tables)} tables)")
        for tbl, (src_c, dst_c) in tables.items():
            total_tables += 1
            total_rows += dst_c
            if src_c != dst_c:
                all_matched = False
                print(f"  ! ERROR in {tbl}: Source={src_c}, Target={dst_c}")

    if all_matched:
        print(f"\nALL {total_tables} TABLES AND {total_rows} ROWS MATCHED 100% PERFECTLY!")
    else:
        print("\nWARNING: Some table row counts did not match. Please review.")


if __name__ == "__main__":
    run_full_migration()

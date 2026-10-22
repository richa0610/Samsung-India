"""Standardize UIDs for demo admins, trainers, and trainees to match the Samsung DB UID conventions.
- AgencyTeam: AGT26NNNNN
- Trainee: TRN26NNNNN, employee_id: EMP26NNN
- Admin: ADM26NNNNN
- Synchronize uid_sequence in tops_demo
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from app.database.common import CommonSessionLocal
from app.database.tenant import tenant_manager

def update_uids():
    common_db = CommonSessionLocal()
    tenant_db = tenant_manager.get_session("demo", common_db)

    try:
        # 1. Update Admin UIDs in Common DB
        print("--- Updating Admin UIDs in Common DB ---")
        admin_updates = [
            ("demoadmin1", "ADM2610008"),
            ("demoadmin2", "ADM2610009"),
        ]
        for username, new_uid in admin_updates:
            common_db.execute(
                text("UPDATE admin SET adminUid = :uid WHERE username = :u"),
                {"uid": new_uid, "u": username}
            )
            print(f"Admin {username} -> {new_uid}")
        common_db.commit()

        # 2. Update Trainers in tops_demo.agencyteam
        print("\n--- Updating Trainer UIDs in tops_demo.agencyteam ---")
        trainer_updates = [
            ("demotrainer1", "AGT2610001", "OFF26000"),
            ("9811122001", "AGT2610002", "OFF26001"),
            ("9811122002", "AGT2610003", "OFF26002"),
            ("9811122003", "AGT2610004", "OFF26003"),
        ]
        for username, new_agt_uid, new_offer_id in trainer_updates:
            tenant_db.execute(
                text("UPDATE agencyteam SET agencyTeamUid = :uid, offerId = :off WHERE username = :u"),
                {"uid": new_agt_uid, "off": new_offer_id, "u": username}
            )
            print(f"Trainer {username} -> agencyTeamUid={new_agt_uid}, offerId={new_offer_id}")

        # 3. Update Trainees in tops_demo.trainee
        print("\n--- Updating Trainee UIDs in tops_demo.trainee ---")
        trainee_updates = [
            ("9822001101", "TRN2610001", "EMP26001"),
            ("9822001102", "TRN2610002", "EMP26002"),
            ("9822001103", "TRN2610003", "EMP26003"),
            ("9822001104", "TRN2610004", "EMP26004"),
        ]
        for phone, new_trn_uid, new_emp_id in trainee_updates:
            tenant_db.execute(
                text("UPDATE trainee SET traineeUid = :uid, uid = :emp WHERE phone = :p"),
                {"uid": new_trn_uid, "emp": new_emp_id, "p": phone}
            )
            print(f"Trainee phone={phone} -> traineeUid={new_trn_uid}, employee_id={new_emp_id}")

        # 4. Synchronize uid_sequence in tops_demo
        print("\n--- Synchronizing tops_demo.uid_sequence ---")
        sequences = [
            ("AGT", 10005),
            ("TRN", 10005),
        ]
        for prefix, next_val in sequences:
            tenant_db.execute(
                text("INSERT INTO uid_sequence (prefix, next_val) VALUES (:p, :nv) "
                     "ON DUPLICATE KEY UPDATE next_val = :nv"),
                {"p": prefix, "nv": next_val}
            )
            print(f"uid_sequence: prefix='{prefix}', next_val={next_val}")

        tenant_db.commit()
        print("\nAll UIDs and sequences updated successfully!")

    finally:
        tenant_db.close()
        common_db.close()

if __name__ == "__main__":
    update_uids()

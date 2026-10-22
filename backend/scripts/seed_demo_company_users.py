"""Seed 2 Admins, 3 Trainers, and 4 Trainees for the 'demo' company tenant.
Run from backend/ with:
    .\\venv\\Scripts\\python.exe scripts/seed_demo_company_users.py

The accounts' password is DEMO_SEED_PASSWORD when that is set; otherwise one is generated and written
to backups/demo-accounts-<time>.txt (git ignores backups/) - never printed, never in the code.
"""

import os
import secrets
import sys
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.database.common import CommonSessionLocal
from app.database.tenant import tenant_manager
from app.models.admin import Admin
from app.models.admin_access import AdminAccess
from app.models.agency_team import AgencyTeam
from app.models.trainee import Trainee
from app.services.access_service import company_admin_key

TENANT_UID = "demo"
COMPANY_NAME = "DEMO Bharat Electronics Pvt Ltd"
BACKUPS = Path(__file__).resolve().parent.parent / "backups"

# 1. Admins to create in Common DB + AdminAccess
ADMINS = [
    {
        "username": "demoadmin1",
        "name": "Vikram Malhotra",
        "email": "vikram.malhotra@demoelectronics.in",
        "phone": 9810011001,
        "role": "admin",
        "access_role": "company_admin",
        "designation": "Head of Operations",
    },
    {
        "username": "demoadmin2",
        "name": "Ananya Sharma",
        "email": "ananya.sharma@demoelectronics.in",
        "phone": 9810011002,
        "role": "admin",
        "access_role": "coordinator",
        "zone": "North Zone",
        "designation": "Zonal Training Coordinator",
    },
]

# 2. Trainers to create in tops_demo.agencyteam
TRAINERS = [
    {
        "username": "9811122001",
        "offerId": "DEMO_TRN_001",
        "name": "Rajesh Khanna",
        "email": "rajesh.khanna@demoelectronics.in",
        "phone": 9811122001,
        "designation": "Senior Technical Trainer",
        "jobCity": "Noida",
        "jobState": "Uttar Pradesh",
    },
    {
        "username": "9811122002",
        "offerId": "DEMO_TRN_002",
        "name": "Pooja Hegde",
        "email": "pooja.hegde@demoelectronics.in",
        "phone": 9811122002,
        "designation": "Product & Soft Skills Trainer",
        "jobCity": "Bengaluru",
        "jobState": "Karnataka",
    },
    {
        "username": "9811122003",
        "offerId": "DEMO_TRN_003",
        "name": "Amitabh Sen",
        "email": "amitabh.sen@demoelectronics.in",
        "phone": 9811122003,
        "designation": "Field Operations Trainer",
        "jobCity": "Mumbai",
        "jobState": "Maharashtra",
    },
]

# 3. Trainees to create in tops_demo.trainee
TRAINEES = [
    {
        "phone": 9822001101,
        "username": "demotrainee1",
        "employee_id": "EMP_DEMO_101",
        "name": "Rohan Gupta",
        "email": "rohan.gupta@demoelectronics.in",
        "gender": "Male",
        "designation": "Sales Executive",
        "district": "New Delhi",
        "state": "Delhi",
        "zone": "North Zone",
        "region": "North 1",
    },
    {
        "phone": 9822001102,
        "username": "demotrainee2",
        "employee_id": "EMP_DEMO_102",
        "name": "Kavita Nair",
        "email": "kavita.nair@demoelectronics.in",
        "gender": "Female",
        "designation": "Product Specialist",
        "district": "Bengaluru",
        "state": "Karnataka",
        "zone": "South Zone",
        "region": "South 1",
    },
    {
        "phone": 9822001103,
        "username": "demotrainee3",
        "employee_id": "EMP_DEMO_103",
        "name": "Arun Joshi",
        "email": "arun.joshi@demoelectronics.in",
        "gender": "Male",
        "designation": "Field Associate",
        "district": "Mumbai",
        "state": "Maharashtra",
        "zone": "West Zone",
        "region": "West 1",
    },
    {
        "phone": 9822001104,
        "username": "demotrainee4",
        "employee_id": "EMP_DEMO_104",
        "name": "Priyanka Sen",
        "email": "priyanka.sen@demoelectronics.in",
        "gender": "Female",
        "designation": "Customer Service Executive",
        "district": "Kolkata",
        "state": "West Bengal",
        "zone": "East Zone",
        "region": "East 1",
    },
]


def _password() -> str:
    """DEMO_SEED_PASSWORD, or a new one written with the usernames to a file in backups/."""
    given = os.environ.get("DEMO_SEED_PASSWORD", "").strip()
    if given:
        return given
    password = secrets.token_urlsafe(12)
    BACKUPS.mkdir(exist_ok=True)
    accounts = BACKUPS / f"demo-accounts-{datetime.now():%Y%m%d-%H%M%S}.txt"
    usernames = [a["username"] for a in ADMINS] + [t["username"] for t in TRAINERS] + [t["username"] for t in TRAINEES]
    accounts.write_text("\n".join([f"Password: {password}", "", *usernames, ""]), encoding="utf-8")
    print(f"Generated a password for the demo accounts - in {accounts}")
    return password


def seed():
    hashed_pwd = hash_password(_password())
    common_db = CommonSessionLocal()
    tenant_db = tenant_manager.get_session(TENANT_UID, common_db)

    try:
        # A. Seed Admins
        print("--- Seeding Admins into Common DB ---")
        for admin_data in ADMINS:
            admin = common_db.query(Admin).filter(Admin.username == admin_data["username"]).first()
            if not admin:
                admin = Admin(
                    adminUid=f"ADM_{uuid.uuid4().hex[:12].upper()}",
                    username=admin_data["username"],
                    name=admin_data["name"],
                    email=admin_data["email"],
                    phone=admin_data["phone"],
                    password=hashed_pwd,
                    role=admin_data["role"],
                    status="Approved",
                    jobStatus="Active",
                    company=COMPANY_NAME,
                    designation=admin_data.get("designation"),
                )
                common_db.add(admin)
                common_db.flush()
                print(f"Created Admin: {admin.username} (ID: {admin.id})")
            else:
                admin.password = hashed_pwd
                admin.status = "Approved"
                admin.company = COMPANY_NAME
                common_db.flush()
                print(f"Updated existing Admin: {admin.username} (ID: {admin.id})")

            # Check AdminAccess grant
            access_role = admin_data["access_role"]
            access_grant = common_db.query(AdminAccess).filter(
                AdminAccess.admin_id == admin.id,
                AdminAccess.tenant_uid == TENANT_UID,
            ).first()

            cak = company_admin_key(TENANT_UID, COMPANY_NAME) if access_role == "company_admin" else None
            if not access_grant:
                access_grant = AdminAccess(
                    admin_id=admin.id,
                    role=access_role,
                    tenant_uid=TENANT_UID,
                    company=COMPANY_NAME,
                    zone=admin_data.get("zone"),
                    active=1,
                    granted_by="system-seed",
                    note=f"Demo seed for {COMPANY_NAME}",
                    company_admin_key=cak,
                )
                common_db.add(access_grant)
                print(f"  Added AdminAccess grant: role={access_role}, tenant={TENANT_UID}")
            else:
                access_grant.active = 1
                access_grant.role = access_role
                access_grant.company = COMPANY_NAME
                access_grant.zone = admin_data.get("zone")
                access_grant.company_admin_key = cak
                print(f"  Updated AdminAccess grant: role={access_role}")

        common_db.commit()

        # B. Seed Trainers in Tenant DB
        print("\n--- Seeding Trainers into Tenant DB (agencyteam) ---")
        for trainer_data in TRAINERS:
            trainer = tenant_db.query(AgencyTeam).filter(
                (AgencyTeam.username == trainer_data["username"]) |
                (AgencyTeam.offerId == trainer_data["offerId"])
            ).first()

            if not trainer:
                trainer = AgencyTeam(
                    agencyTeamUid=f"AT_{uuid.uuid4().hex[:12].upper()}",
                    username=trainer_data["username"],
                    offerId=trainer_data["offerId"],
                    name=trainer_data["name"],
                    email=trainer_data["email"],
                    phone=trainer_data["phone"],
                    password=hashed_pwd,
                    role="trainer",
                    status="Approved",
                    company=COMPANY_NAME,
                    designation=trainer_data["designation"],
                    jobCity=trainer_data["jobCity"],
                    jobState=trainer_data["jobState"],
                )
                tenant_db.add(trainer)
                tenant_db.flush()
                print(f"Created Trainer: {trainer.name} (Username/Phone: {trainer.username}, OfferID: {trainer.offerId})")
            else:
                trainer.password = hashed_pwd
                trainer.role = "trainer"
                trainer.status = "Approved"
                trainer.company = COMPANY_NAME
                trainer.name = trainer_data["name"]
                print(f"Updated existing Trainer: {trainer.name} ({trainer.username})")

        tenant_db.commit()

        # C. Seed Trainees in Tenant DB
        print("\n--- Seeding Trainees into Tenant DB (trainee) ---")
        for t_data in TRAINEES:
            trainee = tenant_db.query(Trainee).filter(
                (Trainee.phone == t_data["phone"]) |
                (Trainee.email == t_data["email"]) |
                (Trainee.username == t_data["username"])
            ).first()

            if not trainee:
                trainee = Trainee(
                    traineeUid=f"TRN_{uuid.uuid4().hex[:12].upper()}",
                    employee_id=t_data["employee_id"],
                    username=t_data["username"],
                    name=t_data["name"],
                    email=t_data["email"],
                    phone=t_data["phone"],
                    gender=t_data["gender"],
                    designation=t_data["designation"],
                    district=t_data["district"],
                    state=t_data["state"],
                    zone=t_data["zone"],
                    region=t_data["region"],
                    company=COMPANY_NAME,
                    password=hashed_pwd,
                    status="Approved",
                    jobStatus="Active",
                )
                tenant_db.add(trainee)
                tenant_db.flush()
                print(f"Created Trainee: {trainee.name} (Phone: {trainee.phone}, EmpID: {trainee.employee_id})")
            else:
                trainee.password = hashed_pwd
                trainee.status = "Approved"
                trainee.jobStatus = "Active"
                trainee.company = COMPANY_NAME
                trainee.username = t_data["username"]
                trainee.employee_id = t_data["employee_id"]
                print(f"Updated existing Trainee: {trainee.name} ({trainee.phone})")

        tenant_db.commit()
        print("\nSeeding completed successfully!")

    finally:
        tenant_db.close()
        common_db.close()


if __name__ == "__main__":
    seed()

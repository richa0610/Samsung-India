"""One-off script to seed a large, realistic batch of demo data across
`trainee`, `conference`, and `attendance` - continues the numbering the
existing seed data (seed_more_trainers.py, plus the 9 trainees / 17
conferences / 20 attendance rows already in the DB) established, rather
than starting a separate parallel dataset. Uses the ORM models directly
since Conference/Trainee/Attendance already cover every column this app
actually uses (see each model's own docstring on why it's a trimmed
mirror of the real table). Run from backend/ with:

    venv/Scripts/python.exe scripts/seed_full_demo_data.py
"""

import json
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.trainee import Trainee

TODAY = date(2026, 8, 27)
DEFAULT_PASSWORD = "Trainee@123"

TRAINERS = [
    ("demotrainer", "Demo Trainer"),
    ("9988770001", "Aditya Kumar"),
    ("9988770002", "Meera Iyer"),
    ("9988770003", "Sanjay Rawat"),
    ("9988770004", "Rohit Verma"),
    ("9988770005", "Sneha Reddy"),
    ("9988770006", "Karan Malhotra"),
    ("9988770007", "Priya Nair"),
    ("9988770008", "Arjun Deshmukh"),
]

# venueUid, Title-Case district (matches how `conference.district` is
# actually stored elsewhere - the venue table's own `district` column is
# a lowercase slug, e.g. "gurugram", used only for the District-picker
# filter, not what gets copied onto conference.district), state
VENUES = [
    ("683de96bdc6d4fc389a0c6ee78e0fd4e", "Noida", "Uttar Pradesh"),
    ("cef5bb061f884690a3f6ecc544dd798c", "Gurugram", "Haryana"),
    ("001ceee02ae94f178bfba170e122737b", "New Delhi", "Delhi"),
    ("d7cc6031264a46a0b189494f91cf82ee", "Lucknow", "Uttar Pradesh"),
    ("0212848bcb1d418c9d5167cbab00a90a", "Faridabad", "Haryana"),
]

STANDARD_TEST_SUITE = "b73524c374fc44159b8ad5d972f61a18"  # Galaxy S26 Product Knowledge (Quiz, 3 Qs)
SURVEY_SUITE = "df1029b81b3c4d60836b50e8464f1515"  # Galaxy S26 Session Feedback Survey (3 Qs)

CHECKLIST_UIDS = {
    "Hall": "7e75a3bfe7114cb397bac08fc800f4ad",
    "Projector": "15e8a3c834214cb08ad6f4bb4c8ea627",
    "Microphone Set": "da0293a09e77427695eae1e6c224f8e2",
    "Attendance Sheet": "89cad2895d91475aae02d3b6fd9243a8",
    "Feedback Forms": "fd4ba6608ac247dbafe8dc987e705c15",
}

AUDIENCE_OPTIONS = ["PC Training", "SEC Plan", "SEC", "SEC LITE GT", "OT SEC", "FESTIVE SEC", "SGC"]
SESSION_TYPE_OPTIONS = ["Classroom Training", "Online Training", "PC Training", "MX Training", "ASE and ZSE", "Sales Team", "Partner Staff"]
TRAINING_TYPE_OPTIONS = ["Webinar", "Product Training", "Classroom Training"]
TRAINING_HUB_OPTIONS = ["Delhi", "BOLPUR", "ALIPURDUAR", "BONGAIGAON", "BAHARAMPUR"]

# ─── City clusters (district/state/zone/region + coords), reused across
# both trainees and conferences so the two datasets feel like one world. ──
CLUSTERS = [
    {"district": "Gurugram", "state": "Haryana", "zone": "North Zone", "region": "North 1", "lat": 28.4595, "lng": 77.0266},
    {"district": "Bengaluru", "state": "Karnataka", "zone": "South Zone", "region": "South 1 [KR]", "lat": 12.9716, "lng": 77.5946},
    {"district": "Pune", "state": "Maharashtra", "zone": "West Zone", "region": "West 1", "lat": 18.5204, "lng": 73.8567},
    {"district": "Mumbai", "state": "Maharashtra", "zone": "West Zone", "region": "West 2", "lat": 19.0760, "lng": 72.8777},
    {"district": "Chennai", "state": "Tamil Nadu", "zone": "South Zone", "region": "South 1 [TN]", "lat": 13.0827, "lng": 80.2707},
    {"district": "Kolkata", "state": "West Bengal", "zone": "East Zone", "region": "East 1", "lat": 22.5726, "lng": 88.3639},
    {"district": "Hyderabad", "state": "Telangana", "zone": "South Zone", "region": "South 2", "lat": 17.3850, "lng": 78.4867},
    {"district": "Jaipur", "state": "Rajasthan", "zone": "North Zone", "region": "North 2", "lat": 26.9124, "lng": 75.7873},
    {"district": "Ahmedabad", "state": "Gujarat", "zone": "West Zone", "region": "West 3", "lat": 23.0225, "lng": 72.5714},
    {"district": "Chandigarh", "state": "Chandigarh", "zone": "North Zone", "region": "North 3", "lat": 30.7333, "lng": 76.7794},
    {"district": "Lucknow", "state": "Uttar Pradesh", "zone": "North Zone", "region": "North 1", "lat": 26.8467, "lng": 80.9462},
    {"district": "Kochi", "state": "Kerala", "zone": "South Zone", "region": "South 3", "lat": 9.9312, "lng": 76.2673},
]

SUPERVISORS = [
    {"uid": "SUP-004", "name": "Vivek Chandran", "designation": "Team Lead"},
    {"uid": "SUP-005", "name": "Anita Krishnan", "designation": "Team Lead"},
    {"uid": "SUP-006", "name": "Suresh Bhattacharya", "designation": "Area Manager"},
    {"uid": "SUP-007", "name": "Farhan Ansari", "designation": "Team Lead"},
]

db = SessionLocal()

try:
    # ═══════════════════════════════════════════════════════════════════
    # PART 1 — 15 new trainees (EMP26010-EMP26024), 10 Approved + 5 Pending
    # ═══════════════════════════════════════════════════════════════════
    TRAINEES = [
        ("Vikram Nair", "Male", "Store Manager"),
        ("Fatima Sheikh", "Female", "Sales Associate"),
        ("Aakash Bhandari", "Male", "Customer Advisor"),
        ("Neha Chawla", "Female", "Retail Executive"),
        ("Suresh Pillai", "Male", "Promoter"),
        ("Ishita Bose", "Female", "Sales Associate"),
        ("Manish Trivedi", "Male", "Customer Advisor"),
        ("Kavya Reddy", "Female", "Retail Executive"),
        ("Ramesh Iyer", "Male", "Store Manager"),
        ("Shreya Kapoor", "Female", "Promoter"),
        ("Ajay Yadav", "Male", "Sales Associate"),
        ("Meenal Kulkarni", "Female", "Customer Advisor"),
        ("Tariq Khan", "Male", "Retail Executive"),
        ("Swati Ghosh", "Female", "Promoter"),
        ("Deepak Choudhary", "Male", "Sales Associate"),
    ]

    created_trainee_uids = []
    for i, (name, gender, designation) in enumerate(TRAINEES):
        seq = 10 + i
        phone = 9123450000 + seq
        existing = db.query(Trainee).filter(Trainee.phone == phone).first()
        if existing:
            print(f"Skipping trainee {name!r} - phone {phone} already exists")
            created_trainee_uids.append(existing.traineeUid)
            continue

        cluster = CLUSTERS[i % len(CLUSTERS)]
        supervisor = SUPERVISORS[i % len(SUPERVISORS)]
        trainer_username, trainer_name = TRAINERS[(i + 2) % len(TRAINERS)]
        slug = name.lower().replace(" ", ".")
        approval_status = "Pending" if i % 3 == 2 else "Approved"  # 5 of 15 Pending
        trainee_uid = uuid.uuid4().hex

        trainee = Trainee(
            traineeUid=trainee_uid,
            name=name,
            email=f"{slug}@example.com",
            phone=phone,
            gender=gender,
            designation=designation,
            supervisorName=supervisor["name"],
            district=cluster["district"],
            state=cluster["state"],
            employee_id=f"EMP260{seq}",
            status=approval_status,
            zone=cluster["zone"].replace(" Zone", ""),
            region=cluster["region"],
            company="Samsung India",
            requestedBy="Quess Corp Ltd",
            trainerEmployeeId=trainer_username,
            trainerName=trainer_name,
            supervisorUid=supervisor["uid"],
            supervisorDesignation=supervisor["designation"],
            agencyId=f"AGY-0{(i % 4) + 4}",
            dob=date(1992 + (i % 8), 1 + (i % 12), 1 + (i % 27)),
            address=f"{100 + i}, MG Road, {cluster['district']}",
            altPhone=str(9123460000 + seq),
            altEmail=f"{slug}.alt@example.com" if i % 2 == 0 else None,
            joinedOn=date(2024, 1 + (i % 12), 1 + (i % 27)),
            jobStatus="Active",
            jobCity=cluster["district"],
            jobPincode=f"{110000 + seq * 11}",
            username=str(phone),
            password=hash_password(DEFAULT_PASSWORD),
            updatedBy="admin",
            updationOn=datetime(2026, 8, 25, 10, 0, 0) + timedelta(hours=i),
        )
        db.add(trainee)
        created_trainee_uids.append(trainee_uid)
        print(f"Created trainee {trainee.employee_id} / {phone} ({name}, {approval_status})")

    db.commit()

    # ═══════════════════════════════════════════════════════════════════
    # PART 2 — 15 new conferences: 5 Ongoing, 5 Completed, 5 Scheduled
    # ═══════════════════════════════════════════════════════════════════
    def session_config(check_in_opens, check_out_closes, st_start, st_end, sv_start, sv_end):
        return json.dumps(
            {
                "attendance": {"checkInOpens": check_in_opens, "checkOutCloses": check_out_closes, "geoFencing": True},
                "standardTest": {
                    "category": "POST TEST",
                    "assessmentSuiteUid": STANDARD_TEST_SUITE,
                    "questionCount": 3,
                    "startTime": st_start,
                    "endTime": st_end,
                    "checkIn": True,
                    "unlockCondition": "Automatic",
                },
                "survey": {
                    "category": "Survey",
                    "assessmentSuiteUid": SURVEY_SUITE,
                    "questionCount": 3,
                    "startTime": sv_start,
                    "endTime": sv_end,
                    "checkIn": True,
                    "unlockCondition": "Automatic",
                },
            }
        )

    checklist_uid = ",".join([CHECKLIST_UIDS["Hall"], CHECKLIST_UIDS["Projector"], CHECKLIST_UIDS["Attendance Sheet"]])

    SESSION_TITLES = [
        "Galaxy S26 Product Deep-Dive",
        "Customer Handling Refresher",
        "Smartphone Sales Techniques",
        "SEC Plan Refresher Workshop",
        "MX Training - Partner Staff Induction",
        "Galaxy AI Feature Walkthrough",
        "Retail Floor Excellence Program",
        "Post-Season Sales Debrief",
        "New Launch Readiness Session",
        "Objection Handling Masterclass",
        "Accessory Bundle Selling Techniques",
        "Trade-In Program Training",
        "Digital Payments & POS Refresher",
        "Premium Segment Selling Skills",
        "Warranty & Service Awareness Session",
    ]

    conference_specs = []

    # 5 Ongoing (today)
    for i in range(5):
        trainer_username, trainer_name = TRAINERS[i % len(TRAINERS)]
        conference_specs.append(
            {
                "conferenceStatus": "Ongoing",
                "status": "Approved",
                "conferenceDate": TODAY.isoformat(),
                "conferenceTime": ["09:00 AM", "10:00 AM", "11:00 AM", "02:00 PM", "03:00 PM"][i],
                "trainer": (trainer_username, trainer_name),
                "title": SESSION_TITLES[i],
                "activeModuleId": ["ATTENDANCE", "STANDARD_TEST", "ATTENDANCE", "SURVEY", "ATTENDANCE"][i],
                "actualStartedAt": datetime.combine(TODAY, datetime.min.time()) + timedelta(hours=9 + i),
                "actualEndedAt": None,
                "conferenceEndsOn": None,
            }
        )

    # 5 Completed (past dates)
    for i in range(5):
        trainer_username, trainer_name = TRAINERS[(i + 3) % len(TRAINERS)]
        past_date = TODAY - timedelta(days=3 + i * 4)
        started = datetime.combine(past_date, datetime.min.time()) + timedelta(hours=9 + i)
        conference_specs.append(
            {
                "conferenceStatus": "Completed",
                "status": "Approved",
                "conferenceDate": past_date.isoformat(),
                "conferenceTime": ["09:00 AM", "10:30 AM", "11:00 AM", "01:00 PM", "03:30 PM"][i],
                "trainer": (trainer_username, trainer_name),
                "title": SESSION_TITLES[5 + i],
                "activeModuleId": None,
                "actualStartedAt": started,
                "actualEndedAt": started + timedelta(hours=2),
                "conferenceEndsOn": (started + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    # 5 Scheduled (future dates), 3 Approved + 2 Pending
    for i in range(5):
        trainer_username, trainer_name = TRAINERS[(i + 6) % len(TRAINERS)]
        future_date = TODAY + timedelta(days=5 + i * 6)
        conference_specs.append(
            {
                "conferenceStatus": "Scheduled",
                "status": "Pending" if i >= 3 else "Approved",
                "conferenceDate": future_date.isoformat(),
                "conferenceTime": ["09:30 AM", "10:00 AM", "02:00 PM", "11:00 AM", "03:00 PM"][i],
                "trainer": (trainer_username, trainer_name),
                "title": SESSION_TITLES[10 + i],
                "activeModuleId": None,
                "actualStartedAt": None,
                "actualEndedAt": None,
                "conferenceEndsOn": None,
            }
        )

    created_conference_uids = {"Ongoing": [], "Completed": [], "Scheduled": []}
    for i, spec in enumerate(conference_specs):
        cluster = CLUSTERS[i % len(CLUSTERS)]
        use_real_venue = i % 3 == 0
        venue_uid, venue_district_key, venue_state = VENUES[i % len(VENUES)] if use_real_venue else (None, None, None)

        conference_uid = uuid.uuid4().hex
        trainer_username, trainer_name = spec["trainer"]
        check_in_opens = spec["conferenceTime"]
        batch_size = str(20 + (i * 3) % 30)

        conference = Conference(
            conferenceUid=conference_uid,
            zone=cluster["zone"],
            region=cluster["region"],
            company="Samsung India",
            requestedBy="Quess Corp Ltd",
            trainerEmployeeId=trainer_username,
            trainerName=trainer_name,
            conferenceType="Residential Conference" if i % 7 == 0 else "Non Residential Conference",
            conferenceDate=spec["conferenceDate"],
            conferenceEndsOn=spec["conferenceEndsOn"],
            conferenceTime=spec["conferenceTime"],
            conferenceStatus=spec["conferenceStatus"],
            activeModuleId=spec["activeModuleId"],
            actualStartedAt=spec["actualStartedAt"],
            actualEndedAt=spec["actualEndedAt"],
            enableCheckIn=1,
            trainingHub=TRAINING_HUB_OPTIONS[i % len(TRAINING_HUB_OPTIONS)],
            audience=AUDIENCE_OPTIONS[i % len(AUDIENCE_OPTIONS)],
            sessionType=SESSION_TYPE_OPTIONS[i % len(SESSION_TYPE_OPTIONS)],
            trainingType=TRAINING_TYPE_OPTIONS[i % len(TRAINING_TYPE_OPTIONS)],
            batchSize=batch_size,
            confirmedPax=batch_size,
            attendanceSheetPax="0",
            suiteTitle=spec["title"],
            state=venue_state or cluster["state"],
            district=(venue_district_key or cluster["district"]),
            venueUid=venue_uid,
            geoLatitude=cluster["lat"],
            geoLongitude=cluster["lng"],
            geoRadius=100,
            postAssessmentUid=STANDARD_TEST_SUITE,
            surveyUid=SURVEY_SUITE,
            noOfQuestion="3",
            sessionConfig=session_config(
                check_in_opens, spec["conferenceTime"], spec["conferenceTime"], spec["conferenceTime"], spec["conferenceTime"], spec["conferenceTime"]
            ),
            checklistUid=checklist_uid,
            updatedBy=trainer_username,
            status=spec["status"],
            remarks="Registered via Add New Training form.",
            timestamp=datetime.combine(TODAY - timedelta(days=1), datetime.min.time()) + timedelta(hours=i),
        )
        db.add(conference)
        created_conference_uids[spec["conferenceStatus"]].append((conference_uid, trainer_username))
        print(f"Created conference {conference_uid[:8]}... [{spec['conferenceStatus']}/{spec['status']}] {spec['title']} ({trainer_name})")

    db.commit()

    # ═══════════════════════════════════════════════════════════════════
    # PART 3 — Attendance: ~20 Present (confirmed) + ~20 Absent (pending)
    # ═══════════════════════════════════════════════════════════════════
    all_trainees = db.query(Trainee).all()

    def make_attendance(conference_uid, trainer_username, trainee, status, marked_at, checkout=None):
        return Attendance(
            attendanceUid=uuid.uuid4().hex,
            conferenceUid=conference_uid,
            trainerUid=trainer_username,
            traineeUid=trainee.traineeUid,
            phone=trainee.phone,
            markedOn=marked_at.strftime("%Y-%m-%d %H:%M:%S"),
            status=status,
            checkOutTime=checkout,
            timestamp=marked_at,
        )

    attendance_count = {"Present": 0, "Absent": 0}
    trainee_pool_index = 0

    for conference_uid, trainer_username in created_conference_uids["Completed"]:
        base_time = datetime.combine(TODAY - timedelta(days=10), datetime.min.time())
        for j in range(4):
            trainee = all_trainees[trainee_pool_index % len(all_trainees)]
            trainee_pool_index += 1
            marked_at = base_time + timedelta(minutes=j * 5)
            status = "Absent" if j == 3 else "Present"
            checkout = marked_at + timedelta(hours=2) if status == "Present" else None
            existing = (
                db.query(Attendance)
                .filter(Attendance.conferenceUid == conference_uid, Attendance.traineeUid == trainee.traineeUid)
                .first()
            )
            if existing:
                continue
            db.add(make_attendance(conference_uid, trainer_username, trainee, status, marked_at, checkout))
            attendance_count[status] += 1

    for conference_uid, trainer_username in created_conference_uids["Ongoing"]:
        base_time = datetime.combine(TODAY, datetime.min.time()) + timedelta(hours=9)
        for j in range(3):
            trainee = all_trainees[trainee_pool_index % len(all_trainees)]
            trainee_pool_index += 1
            marked_at = base_time + timedelta(minutes=j * 5)
            status = "Absent" if j == 2 else "Present"
            existing = (
                db.query(Attendance)
                .filter(Attendance.conferenceUid == conference_uid, Attendance.traineeUid == trainee.traineeUid)
                .first()
            )
            if existing:
                continue
            db.add(make_attendance(conference_uid, trainer_username, trainee, status, marked_at))
            attendance_count[status] += 1

    db.commit()
    print(f"Attendance seeded this run: Present={attendance_count['Present']}, Absent={attendance_count['Absent']}")

finally:
    db.close()

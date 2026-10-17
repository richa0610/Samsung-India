"""Registers one company in the shared `agency` table - where every client company is registered
first (user, 2026-10-14) - from a JSON file whose keys are the table's own column names:

    {"agency": {"companyName": "...", "name": "<contact person>", "email": "...", "phone": "9876543210",
                "website": "...", "localCity": "...", "localDistrict": "...", "localState": "...",
                "localPinCode": "411001", "aboutAgency": "..."}}

    cd backend
    venv/Scripts/python.exe scripts/add_agency.py scripts/agency.demo.json            # preview - writes nothing
    venv/Scripts/python.exe scripts/add_agency.py scripts/agency.demo.json --apply    # add it
    venv/Scripts/python.exe scripts/add_agency.py --undo backups/agency-<...>.json    # remove exactly that row

companyName, name, email and phone are required. Before anything is written it refuses a company
already registered under any spelling of its name, an email or phone another agency already
uses, a malformed phone / email / PIN code, and any key that isn't one of the columns above. The
row is added Pending with a new agencyUid ("AGY" + year + 5 random digits, checked unused); what
--apply added is saved to backups/ before it is committed, and --undo removes that row only while
it is still marked as added by this script.
"""

import argparse
import json
import re
import secrets
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.models.agency import Agency  # noqa: E402
from app.utils.date_utils import ist_now  # noqa: E402

ADDED_BY = "system:add-agency"
PENDING = "Pending"
BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
UID_PREFIX = "AGY"
UID_ATTEMPTS = 25

REQUIRED = ("companyName", "name", "email", "phone")
OPTIONAL = ("website", "localCity", "localDistrict", "localState", "localPinCode", "aboutAgency")
_PHONE = re.compile(r"^[6-9]\d{9}$")
_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PIN = re.compile(r"^\d{6}$")
# A template's "<fill this in>" value (scripts/agency.samsung.json) - never saved as data.
_PLACEHOLDER = re.compile(r"^<.*>$")


def _clean(value) -> str:
    return " ".join(str(value).split())


def _name_key(name: Optional[str]) -> str:
    """How two spellings of one company name compare: inner spacing collapsed, any letter case."""
    return _clean(name or "").lower()


def load_agency(path: Path) -> tuple[dict, list[str]]:
    """The file's agency, tidied, and what is wrong with it (empty when nothing is)."""
    data = json.loads(path.read_text(encoding="utf-8")).get("agency")
    if not isinstance(data, dict):
        return {}, ['The file needs an "agency" object.']
    unknown = sorted(set(data) - set(REQUIRED) - set(OPTIONAL))
    agency = {key: _clean(value) for key, value in data.items() if key in REQUIRED + OPTIONAL and value is not None}
    problems = [f"Unknown field(s): {', '.join(unknown)}"] if unknown else []
    problems += [f"{key} is required" for key in REQUIRED if not agency.get(key)]
    problems += [f"{key} still holds the placeholder {value}" for key, value in agency.items() if _PLACEHOLDER.match(value)]
    if agency.get("phone") and not _PHONE.match(agency["phone"]):
        problems.append("phone must be a 10-digit mobile number")
    if agency.get("email") and not _EMAIL.match(agency["email"]):
        problems.append("email doesn't look like an email address")
    if agency.get("localPinCode") and not _PIN.match(agency["localPinCode"]):
        problems.append("localPinCode must be 6 digits")
    return agency, problems


def conflicts(db: Session, agency: dict) -> list[str]:
    """Agencies already registered under this company name (any spelling - compared here, as SQL
    can't collapse inner spaces; the table holds one row per company), email or phone."""
    name, email, phone = _name_key(agency["companyName"]), agency["email"].lower(), int(agency["phone"])
    rows = db.query(Agency.agencyUid, Agency.companyName, Agency.email, Agency.phone)
    return [
        f"Already registered: {uid} {company!r} ({row_email}, {row_phone})"
        for uid, company, row_email, row_phone in rows
        if _name_key(company) == name or (row_email or "").strip().lower() == email or row_phone == phone
    ]


def preview(db: Session, path: Path) -> tuple[dict, list[str]]:
    """Prints the row --apply would add and returns it with any reason it can't be added."""
    agency, problems = load_agency(path)
    if not problems:
        problems = conflicts(db, agency)
    print("Agency to register:")
    for key in REQUIRED + OPTIONAL:
        if agency.get(key):
            print(f"  {key:<14} {agency[key]}")
    print(f"  {'status':<14} {PENDING}")
    return agency, problems


def _new_uid(db: Session) -> str:
    year = f"{ist_now().year % 100:02d}"
    for _ in range(UID_ATTEMPTS):
        uid = f"{UID_PREFIX}{year}{secrets.randbelow(10 ** 5):05d}"
        if db.query(Agency.id).filter(Agency.agencyUid == uid).first() is None:
            return uid
    raise SystemExit("Could not find an unused agencyUid - nothing written.")


def apply(db: Session, agency: dict) -> tuple[str, Path]:
    """Adds the agency (Pending, marked as this script's) and saves its agencyUid to backups/
    before committing."""
    row = Agency(
        **{key: agency[key] for key in REQUIRED + OPTIONAL if agency.get(key) and key != "phone"},
        phone=int(agency["phone"]),
        agencyUid=_new_uid(db),
        status=PENDING,
        updatedBy=ADDED_BY,
        remarks=f"Registered by scripts/add_agency.py on {datetime.now():%Y-%m-%d}",
    )
    db.add(row)
    db.flush()
    BACKUP_DIR.mkdir(exist_ok=True)
    backup = BACKUP_DIR / f"agency-{row.agencyUid}-{datetime.now():%Y%m%d-%H%M%S}.json"
    backup.write_text(json.dumps({"agencyUid": row.agencyUid, "companyName": row.companyName}, indent=2), encoding="utf-8")
    db.commit()
    return row.agencyUid, backup


def undo(db: Session, backup: Path) -> int:
    """Removes the agency a backup names, only while it is still marked as added by this script."""
    saved = json.loads(backup.read_text(encoding="utf-8"))
    removed = (
        db.query(Agency)
        .filter(Agency.agencyUid == saved["agencyUid"], Agency.updatedBy == ADDED_BY)
        .delete(synchronize_session=False)
    )
    db.commit()
    return removed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", type=Path, help="the JSON file of the agency to register")
    parser.add_argument("--apply", action="store_true", help="add it (default: preview only)")
    parser.add_argument("--undo", type=Path, metavar="BACKUP", help="remove exactly the agency a backup names")
    args = parser.parse_args()
    if bool(args.file) == bool(args.undo):
        parser.error("give either the agency file or --undo BACKUP")

    from app.database.common import CommonSessionLocal  # local: needs the app's settings, never the test ones

    db = CommonSessionLocal()
    try:
        if args.undo:
            print(f"Removed {undo(db, args.undo)} agency row(s) listed in {args.undo.name}.")
            return
        agency, problems = preview(db, args.file)
        if problems:
            raise SystemExit("\nStopped - nothing written:\n  " + "\n  ".join(problems))
        if not args.apply:
            print("\nPreview only - nothing written. Run again with --apply to add it.")
            return
        uid, backup = apply(db, agency)
        print(f"\nRegistered {uid}. Undo file: {backup}")
    finally:
        db.close()


if __name__ == "__main__":
    main()

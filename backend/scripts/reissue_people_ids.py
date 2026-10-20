"""Gives a company's trainees and trainers new IDs and HO IDs that no other company uses, so they can
join the central user registry (user, 2026-10-20: the demo company's people repeated Samsung's).

New IDs come from the shared counters in the Common DB (services/user_registry_service): a trainee's
from its zone (or TRN), a trainer's AGT - each above every number any company has used. New HO IDs
are <TENANT>-EMP-001... for trainees and <TENANT>-OFF-001... for trainers. Names, usernames, phones and
passwords stay, and so does everything that names a person by username (a training's trainer, a
trainee's assigned trainer). Refused for the default company, and for a company that has attendance,
answers or results recorded against the old IDs - those aren't rewritten.

DRY RUN by default: reads only, and prints each person's old and new IDs. --apply saves the old values
to backend/backups/<tenant>-people-ids-<time>.json first, then writes; --undo <that file> puts them
back. The company database is opened without the app's pool or schema sync (scripts/_tenant_db.py).

    cd backend
    venv/Scripts/python.exe scripts/reissue_people_ids.py --tenant demo
    venv/Scripts/python.exe scripts/reissue_people_ids.py --tenant demo --apply
    venv/Scripts/python.exe scripts/reissue_people_ids.py --undo backups/demo-people-ids-20261020-120000.json
"""

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, ".")
from scripts._tenant_db import tenant_engine  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.models import uid_events  # noqa: E402
from app.models.agency_team import AgencyTeam  # noqa: E402
from app.models.attendance import Attendance  # noqa: E402
from app.models.quiz import Assessment, AssessmentResult  # noqa: E402
from app.models.trainee import Trainee  # noqa: E402
from app.repositories import user_registry_repository as registry  # noqa: E402
from app.services import user_registry_service  # noqa: E402
from app.utils.date_utils import ist_now  # noqa: E402

BACKUPS = Path("backups")


@dataclass
class Change:
    table: str   # trainee / agencyteam
    row_id: int
    username: str | None
    old_uid: str | None
    old_hoid: str | None
    new_uid: str
    new_hoid: str


def _people(tenant_db: Session) -> tuple[list[Trainee], list[AgencyTeam]]:
    return (tenant_db.query(Trainee).order_by(Trainee.id).all(), tenant_db.query(AgencyTeam).order_by(AgencyTeam.id).all())


def _refuse_unless_safe(tenant_db: Session, tenant_uid: str) -> None:
    if tenant_uid == settings.DEFAULT_TENANT_ID:
        raise SystemExit(f"Refused: {tenant_uid} is the default company - its people keep their IDs.")
    for model in (Attendance, Assessment, AssessmentResult):
        if tenant_db.query(model).count():
            raise SystemExit(f"Refused: {tenant_uid} has {model.__tablename__} rows recorded against the old IDs.")


def _hoids(tenant_uid: str, trainees: list, trainers: list) -> tuple[list[str], list[str]]:
    code = tenant_uid.strip().upper()
    return ([f"{code}-EMP-{n:03d}" for n in range(1, len(trainees) + 1)],
            [f"{code}-OFF-{n:03d}" for n in range(1, len(trainers) + 1)])


def _check_hoids_free(common_db: Session, hoids: list[str], own_uids: set[str]) -> None:
    for hoid in hoids:
        holder = registry.holder(common_db, "hoid", hoid)
        if holder is not None and holder.user_uid.lower() not in own_uids:
            raise SystemExit(f"Refused: HO ID {hoid} is already registered to {holder.user_uid}.")


def plan_reissue(common_db: Session, tenant_db: Session, tenant_uid: str, open_tenant) -> list[Change]:
    """The changes --apply would make - reading only: each shared counter's next number (or, for a
    counter not started yet, the first number no company has used)."""
    _refuse_unless_safe(tenant_db, tenant_uid)
    trainees, trainers = _people(tenant_db)
    trainee_hoids, trainer_hoids = _hoids(tenant_uid, trainees, trainers)
    _check_hoids_free(common_db, trainee_hoids + trainer_hoids, set())
    next_number: dict[str, int] = {}

    def preview(prefix: str, column) -> str:
        if prefix not in next_number:
            current = common_db.execute(text("SELECT next_val FROM uid_sequence WHERE prefix = :p"), {"p": prefix}).scalar()
            next_number[prefix] = current or user_registry_service.first_unused_in_companies(common_db, prefix, open_tenant, column)
        number, next_number[prefix] = next_number[prefix], next_number[prefix] + 1
        return f"{prefix}{ist_now().year % 100:02d}{number:05d}"

    return [
        Change("trainee", t.id, t.username, t.traineeUid, t.employee_id,
               preview(uid_events.trainee_uid_prefix(t.zone), Trainee.traineeUid), hoid)
        for t, hoid in zip(trainees, trainee_hoids)
    ] + [
        Change("agencyteam", a.id, a.username, a.agencyTeamUid, a.offerId,
               preview(uid_events.TRAINER_UID_PREFIX, AgencyTeam.agencyTeamUid), hoid)
        for a, hoid in zip(trainers, trainer_hoids)
    ]


def apply_reissue(common_db: Session, tenant_db: Session, tenant_uid: str, open_tenant, backup_dir: Path = BACKUPS) -> tuple[list[Change], Path]:
    """Claims the new IDs from the shared counters, saves every old and new value, then writes them."""
    _refuse_unless_safe(tenant_db, tenant_uid)
    trainees, trainers = _people(tenant_db)
    trainee_hoids, trainer_hoids = _hoids(tenant_uid, trainees, trainers)
    _check_hoids_free(common_db, trainee_hoids + trainer_hoids, set())
    changes = [
        Change("trainee", t.id, t.username, t.traineeUid, t.employee_id, user_registry_service.claim_trainee_uid(common_db, t.zone, open_tenant), hoid)
        for t, hoid in zip(trainees, trainee_hoids)
    ] + [
        Change("agencyteam", a.id, a.username, a.agencyTeamUid, a.offerId, user_registry_service.claim_trainer_uid(common_db, open_tenant), hoid)
        for a, hoid in zip(trainers, trainer_hoids)
    ]
    common_db.commit()   # the numbers are taken; a failure below only leaves them unused

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f"{tenant_uid}-people-ids-{datetime.now():%Y%m%d-%H%M%S}.json"
    backup.write_text(json.dumps({"tenant": tenant_uid, "changes": [asdict(c) for c in changes]}, indent=2), encoding="utf-8")

    for change, person in zip(changes, trainees + trainers):
        if change.table == "trainee":
            person.traineeUid, person.employee_id = change.new_uid, change.new_hoid
        else:
            person.agencyTeamUid, person.offerId = change.new_uid, change.new_hoid
    tenant_db.commit()
    return changes, backup


def undo_reissue(tenant_db: Session, backup: dict) -> int:
    """Puts back the old IDs a backup recorded - only on a row that still has the new ones."""
    restored = 0
    for change in (Change(**c) for c in backup["changes"]):
        model, uid_col, hoid_attr = (Trainee, "traineeUid", "employee_id") if change.table == "trainee" else (AgencyTeam, "agencyTeamUid", "offerId")
        person = tenant_db.get(model, change.row_id)
        if person is None or getattr(person, uid_col) != change.new_uid:
            print(f"  left alone: {change.table} {change.row_id} - changed since")
            continue
        setattr(person, uid_col, change.old_uid)
        setattr(person, hoid_attr, change.old_hoid)
        restored += 1
    tenant_db.commit()
    return restored


def main() -> None:
    parser = argparse.ArgumentParser(description="Give a company's people IDs no other company uses (dry run unless --apply).")
    parser.add_argument("--tenant", help="the company (its tenant ID)")
    parser.add_argument("--apply", action="store_true", help="write the new IDs (default: dry run)")
    parser.add_argument("--undo", type=Path, help="put back the old IDs a backup file recorded")
    args = parser.parse_args()
    if bool(args.tenant) == bool(args.undo):
        parser.error("give --tenant (dry run / --apply) or --undo <backup file>")

    from app.database.common import CommonSessionLocal

    backup = json.loads(args.undo.read_text(encoding="utf-8")) if args.undo else None
    tenant_uid = backup["tenant"] if backup else args.tenant
    engines = []

    def open_tenant(uid: str) -> Session:
        engines.append(tenant_engine(uid))
        return sessionmaker(bind=engines[-1])()

    common_db, tenant_db = CommonSessionLocal(), open_tenant(tenant_uid)
    try:
        if backup:
            print(f"{tenant_uid}: restored {undo_reissue(tenant_db, backup)} people. Run scripts/sync_user_registry.py to update the registry.")
            return
        if args.apply:
            changes, path = apply_reissue(common_db, tenant_db, tenant_uid, open_tenant)
        else:
            changes = plan_reissue(common_db, tenant_db, tenant_uid, open_tenant)
            common_db.rollback()
        for c in changes:
            print(f"  {c.table:10} {c.username or '-':14} {c.old_uid} -> {c.new_uid}   HO ID {c.old_hoid} -> {c.new_hoid}")
        print(f"applied - old values saved to {path}" if args.apply else "dry run - nothing was written. Run again with --apply.")
    finally:
        tenant_db.close()
        common_db.close()
        for engine in engines:
            engine.dispose()


if __name__ == "__main__":
    main()

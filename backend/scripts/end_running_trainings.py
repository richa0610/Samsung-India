"""Ends trainings left running ("Ongoing" / "Live") the way a trainer's End Session does
(services/training/session_control.end_training) - minus the trainer's check-out photo and signed
attendance sheet, which only the trainer's own device can provide:

  - the live module, if any, is stopped - a Live Quiz is scored first, so everyone who answered
    gets their result, exactly as when a trainer ends it
  - the training is marked Completed with its end time (conferenceEndsOn / actualEndedAt; one
    already stamped keeps its time)
  - its Execution Flow gets the STOPPED / SESSION_ENDED lines, marked as an admin data fix, and the
    activity log an END_SESSION row

    cd backend
    venv/Scripts/python.exe scripts/end_running_trainings.py                        # list them - writes nothing
    venv/Scripts/python.exe scripts/end_running_trainings.py --end CONF1 CONF2 ...  # end exactly these

Only the trainings named after --end are ended, and only if they are still running at that moment -
one a trainer starts after the list was printed is never touched. Their state before is saved to
backups/ first.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app.models  # noqa: E402,F401 - registers every table and its hooks
from app.models.attendance import Attendance  # noqa: E402
from app.models.conference import Conference  # noqa: E402
from app.models.conference_activity_log import ConferenceActivityLog  # noqa: E402
from app.services import live_quiz_service  # noqa: E402
from app.services.activity_log_service import log_activity  # noqa: E402
from app.services.module_flow import log_module_action  # noqa: E402
from app.utils.date_utils import utc_now  # noqa: E402
from scripts._tenant_db import tenant_engine  # noqa: E402

PERFORMED_BY = "system:admin-data-fix"
REMARK = "Ended by an admin data fix - left running; no trainer check-out photo or attendance sheet"
BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
_RUNNING = ("ongoing", "live")
_BEFORE_FIELDS = ("conferenceStatus", "conferenceEndsOn", "actualEndedAt", "activeModuleId", "liveQuizState")


def running(db: Session) -> list[Conference]:
    """Trainings whose status says they are running (any letter case), oldest first."""
    return (
        db.query(Conference)
        .filter(func.lower(func.coalesce(Conference.conferenceStatus, "")).in_(_RUNNING))
        .order_by(Conference.id)
        .all()
    )


def describe(db: Session, conference: Conference) -> dict:
    """What the list shows for one training - enough to tell a forgotten one from a real one."""
    uid = conference.conferenceUid
    return {
        "conferenceUid": uid,
        "date": conference.conferenceDate,
        "time": conference.conferenceTime,
        "trainer": conference.trainerEmployeeId,
        "activeModule": conference.activeModuleId,
        "participants": db.query(func.count(Attendance.id)).filter(Attendance.conferenceUid == uid).scalar(),
        "lastActivity": db.query(func.max(ConferenceActivityLog.timestamp))
        .filter(ConferenceActivityLog.conferenceUid == uid)
        .scalar(),
    }


def before_state(conference: Conference) -> dict:
    return {field: _plain(getattr(conference, field)) for field in _BEFORE_FIELDS}


def _plain(value):
    return value.isoformat() if isinstance(value, datetime) else value


def end(db: Session, conference: Conference) -> None:
    """Ends one running training (see the module docstring)."""
    uid = conference.conferenceUid
    now = utc_now()
    active = conference.activeModuleId
    if active:
        if active == "LIVE_QUIZ":
            live_quiz_service.finish_quiz(db, conference)  # scores everyone who answered; commits
        log_module_action(db, uid, active, "STOPPED", PERFORMED_BY, location_remark=REMARK)
        conference.activeModuleId = None
    log_module_action(db, uid, None, "SESSION_ENDED", PERFORMED_BY, location_remark=REMARK)
    conference.conferenceEndsOn = conference.conferenceEndsOn or now.strftime("%Y-%m-%d %H:%M:%S")
    conference.actualEndedAt = conference.actualEndedAt or now
    conference.conferenceStatus = "Completed"
    db.commit()
    log_activity(db, action="END_SESSION", username=PERFORMED_BY, role="admin",
                 remarks=f"Ended training {uid} - {REMARK}")


def end_named(db: Session, uids: list[str]) -> tuple[list[dict], list[str]]:
    """Ends each named training that is still running; returns (the ended ones' state before,
    the names that weren't running and were skipped)."""
    still_running = {c.conferenceUid: c for c in running(db)}
    targets = [still_running[uid] for uid in uids if uid in still_running]
    skipped = [uid for uid in uids if uid not in still_running]
    before = [{"conferenceUid": c.conferenceUid, **before_state(c)} for c in targets]
    for conference in targets:
        end(db, conference)
    return before, skipped


def main() -> None:
    from app.core.config import settings

    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--tenant", default=settings.DEFAULT_TENANT_ID)
    parser.add_argument("--end", nargs="+", metavar="CONFERENCE_UID", help="end exactly these trainings")
    args = parser.parse_args()

    engine = tenant_engine(args.tenant)
    print(f"Tenant {args.tenant!r} - database {engine.url.render_as_string(hide_password=True)}\n")
    with sessionmaker(bind=engine)() as db:
        if not args.end:
            trainings = [describe(db, c) for c in running(db)]
            print(f"{len(trainings)} training(s) still running:\n")
            for t in trainings:
                print(f"  {t['conferenceUid']}  date {t['date']} {t['time'] or ''}  trainer {t['trainer']}  "
                      f"active {t['activeModule'] or '-'}  participants {t['participants']}  last activity {t['lastActivity']}")
            if trainings:
                print("\nNothing written. To end them:\n  venv/Scripts/python.exe scripts/end_running_trainings.py --end "
                      + " ".join(t["conferenceUid"] for t in trainings))
            return

        BACKUP_DIR.mkdir(exist_ok=True)
        backup = BACKUP_DIR / f"end-running-trainings-{args.tenant}-{datetime.now():%Y%m%d-%H%M%S}.json"
        snapshot = [{"conferenceUid": c.conferenceUid, **before_state(c)} for c in running(db) if c.conferenceUid in args.end]
        backup.write_text(json.dumps({"tenant": args.tenant, "before": snapshot}, indent=2), encoding="utf-8")
        print(f"Saved their state before to {backup}\n")
        ended, skipped = end_named(db, args.end)
        for t in ended:
            print(f"  ended {t['conferenceUid']}")
        for uid in skipped:
            print(f"  skipped {uid} - not running (already ended, or no such training)")


if __name__ == "__main__":
    main()

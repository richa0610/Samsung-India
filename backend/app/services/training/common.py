"""What the training modules share: the one access check for a single training, the live-room nudge
after a trainer action, and the short TrainingOut answer most actions return."""

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.conference import Conference
from app.routers.ws import manager as ws_manager
from app.schemas.training import TrainingOut
from app.services import conference_access


def owned_conference(
    db: Session, admin: Admin, conference_uid: str, common_db: Session = None, tenant_id: str = None
) -> Conference:
    """Write access to one conference: the trainer it's assigned to, or - per the approved
    Phase C access grants (`admin_access`, see access_service.resolve_scope) - an admin-table
    account whose grant covers this conference's company/zone/region: Super Admin any session,
    Company Admin their company, Coordinator their zone, Sub-coordinator their region. They
    operate it exactly like the assigned trainer (same approval/schedule/geofence/photo rules);
    only who is allowed to press the buttons changes.
    The rule itself lives in conference_access (shared with live_quiz_service and the WebSocket
    room). It fails closed: a missing `tenant_id` denies everyone, a missing `common_db` denies an
    admin-table account, and a trainer must be an active trainer in this tenant."""
    return conference_access.get_authorized_conference(db, admin, conference_uid, common_db, tenant_id)


def nudge_session_room(background_tasks: BackgroundTasks, conference_uid: str, tenant_id: str = None) -> None:
    """Tell everyone on the conference's `/ws/live` room (the trainees) to
    refetch `/sessions/current`. Fired after any trainer action that changes
    what a trainee sees - starting/stopping a module, marking attendance,
    starting/ending the session - so their screen updates in real time
    instead of waiting for the 10s poll. The payload is a thin nudge; the
    real state travels over REST.

    `tenant_id` scopes both the room and the admin-panel broadcast to the caller's own tenant
    (see routers/ws.py) - a caller that omits it (only possible from a direct internal call, not
    through a router) sends no notification at all rather than one with no tenant to route by."""
    background_tasks.add_task(ws_manager.send_to_room, tenant_id, conference_uid, {"type": "session"})
    background_tasks.add_task(ws_manager.broadcast, tenant_id, {"type": "training_status_changed", "conferenceUid": conference_uid})


def training_out(conference: Conference) -> TrainingOut:
    """The answer to a training action: its ID, run status and approval status."""
    return TrainingOut(
        conferenceUid=conference.conferenceUid,
        conferenceStatus=conference.conferenceStatus,
        status=conference.status,
    )

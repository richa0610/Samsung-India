"""The one rule for "may this caller open or operate this conference" - shared by every
conference-level endpoint (training_service), the Live Quiz controls (live_quiz_service) and the
live WebSocket room (routers/ws.py), so none of them keeps its own copy.

    verified principal + verified tenant  ->  access_service.resolve_scope
                                          ->  dashboard_repository.conference_authorization_conditions
                                          ->  conference_repository.get_authorized (conditions in the WHERE)

An admin-panel account reaches conferences inside its admin_access grant; an active trainer
reaches the conferences assigned to them; anyone else reaches none. Out of scope, wrong tenant
and nonexistent all look the same to the caller."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import not_found
from app.models.conference import Conference
from app.repositories import conference_repository, dashboard_repository
from app.services.access_service import resolve_scope


def find_authorized_conference(
    db: Session, principal: object, conference_uid: str, common_db: Optional[Session], tenant_id: Optional[str]
) -> Optional[Conference]:
    scope = resolve_scope(common_db, principal, tenant_id)
    conditions = dashboard_repository.conference_authorization_conditions(scope)
    return conference_repository.get_authorized(db, conference_uid, conditions)


def get_authorized_conference(
    db: Session, principal: object, conference_uid: str, common_db: Optional[Session], tenant_id: Optional[str]
) -> Conference:
    conference = find_authorized_conference(db, principal, conference_uid, common_db, tenant_id)
    if conference is None:
        raise not_found("Training not found")
    return conference

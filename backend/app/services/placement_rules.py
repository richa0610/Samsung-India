"""Who may put a record (a training, or a newly registered trainee) in a company/zone/region and
assign it a trainer - one rule, used by training creation, training edits and trainee
registration alike (approved business rules, see the Trainer Flow Phase 2.2 decisions):

  - An active trainer places records in their OWN company only (from their account, never the
    form), and may assign themselves or another active trainer of that same company. A trainer
    whose company is unknown may only assign themselves.
  - An admin-panel account places records only inside their admin_access grant
    (company/zone/region, `reject_outside_scope`), and may assign only an active trainer of this
    tenant whose company is one of the companies the grant covers. A Super Admin: any active
    trainer of this tenant.
  - Anyone else is refused.

The assigned trainer is only checked when it changes (`current_trainer`), so editing an older
record keeps working even if its trainer predates these rules. Every refusal is a 403 that names
no record the caller can't see."""

from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import forbidden
from app.models.admin import Admin
from app.models.agency_team import AgencyTeam
from app.services import trainer_service
from app.services.access_service import AccessScope, norm, reject_outside_scope


def authorize_placement(
    db: Session,
    common_db: Optional[Session],
    principal: Admin | AgencyTeam,
    scope: AccessScope,
    tenant_id: Optional[str],
    *,
    company: Optional[str],
    zone: Optional[str],
    region: Optional[str],
    trainer: Optional[str],
    current_trainer: Optional[str] = None,
) -> None:
    assigned = (trainer or "").strip()
    trainer_changed = bool(assigned) and assigned != (current_trainer or "").strip()
    if scope.is_trainer:
        _authorize_trainer(db, common_db, principal, scope.trainer_username, tenant_id, company, assigned, trainer_changed)
    elif scope.is_admin_panel:
        _authorize_admin(db, common_db, scope, tenant_id, company, zone, region, assigned, trainer_changed)
    else:
        raise forbidden("This action requires an active trainer account")


def _authorize_trainer(db, common_db, principal, own_username: str, tenant_id, company, assigned: str, trainer_changed: bool):
    own_company = norm(principal.company)
    if own_company and norm(company) != own_company:
        raise forbidden("This company is outside your authorized scope")
    if not trainer_changed or assigned == own_username:
        return
    target = trainer_service.find_trainer(common_db, db, assigned, tenant_id)
    if not own_company or target is None or norm(target.company) != own_company:
        raise forbidden("You can only assign a trainer from your own company")


def _authorize_admin(db, common_db, scope: AccessScope, tenant_id, company, zone, region, assigned: str, trainer_changed: bool):
    reject_outside_scope(scope, company, zone, region)
    if not trainer_changed:
        return
    target = trainer_service.find_trainer(common_db, db, assigned, tenant_id)
    if target is None:
        raise forbidden("This trainer is not an active trainer in this organisation")
    if not scope.is_super and norm(target.company) not in {rule.company for rule in scope.rules}:
        raise forbidden("You can only assign a trainer from a company in your authorized scope")

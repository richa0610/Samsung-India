from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request, forbidden
from app.core.security import hash_password
from app.models.admin import Admin
from app.models.trainee import Trainee
from app.repositories import dashboard_repository, trainee_repository
from app.routers.ws import manager as ws_manager
from app.schemas.trainee_admin import TraineeAdminIn, TraineeAdminOut
from app.services.access_service import AccessScope, norm, resolve_scope
from app.services.activity_log_service import log_activity
from app.utils.status import title_status


def _trainee_to_admin_out(t: Trainee) -> TraineeAdminOut:
    return TraineeAdminOut(
        traineeUid=t.traineeUid,
        registeredAt=t.timestamp.strftime("%Y-%m-%d %H:%M:%S") if t.timestamp else "",
        approvalStatus=title_status(t.status),
        profilePhoto=t.profilePhoto,
        agencyId=t.agencyId,
        fullName=t.name,
        designation=t.designation,
        gender=t.gender,
        dob=t.dob.isoformat() if t.dob else None,
        primaryEmail=t.email,
        primaryPhone=str(t.phone),
        altEmail=t.altEmail,
        altPhone=t.altPhone,
        address=t.address,
        state=t.state,
        district=t.district,
        zone=t.zone,
        region=t.region,
        company=t.company,
        requestedBy=t.requestedBy,
        trainerId=t.trainerEmployeeId,
        trainerName=t.trainerName,
        supervisorId=t.supervisorUid,
        supervisorName=t.supervisorName,
        supervisorDesignation=t.supervisorDesignation,
        joinedOn=t.joinedOn.isoformat() if t.joinedOn else None,
        jobStatus=t.jobStatus,
        jobCity=t.jobCity,
        jobPincode=t.jobPincode,
        resignedOn=t.resignedOn.isoformat() if t.resignedOn else None,
        username=t.username,
        updatedBy=t.updatedBy,
        updationOn=t.updationOn.strftime("%Y-%m-%d %H:%M:%S") if t.updationOn else None,
        timestamp=t.timestamp.strftime("%Y-%m-%d %H:%M:%S") if t.timestamp else None,
    )


def _reject_forged_scope(scope: AccessScope, payload: TraineeAdminIn) -> None:
    """Company/zone/region come from the request body, same as every other field on this form -
    but unlike the rest of the form, these three double as an authorization boundary elsewhere
    (the Training List, the Attendance list, this same trainee list). A Company Admin, a
    Coordinator or a Sub-coordinator holds exactly one company (and, for the latter two, exactly
    one zone or region) - so a payload naming a different one isn't a data-entry mistake, it's a
    forged scope value, and is rejected outright rather than silently corrected. A Super Admin
    holds no single company/zone/region to check against, so nothing here applies to them; an
    account with no rule at all (no grant, or a trainer) has nothing to compare against either -
    this only narrows an admin who actually holds one of these grants."""
    if scope.is_super or not scope.rules:
        return
    companies = {rule.company for rule in scope.rules}
    if len(companies) == 1 and norm(payload.company) not in companies:
        raise forbidden("This company is outside your authorized scope")
    zones = {rule.zone for rule in scope.rules if rule.zone is not None}
    if zones and norm(payload.zone) not in zones:
        raise forbidden("This zone is outside your authorized scope")
    regions = {rule.region for rule in scope.rules if rule.region is not None}
    if regions and norm(payload.region) not in regions:
        raise forbidden("This region is outside your authorized scope")


def register_trainee_admin(
    db: Session,
    payload: TraineeAdminIn,
    background_tasks: BackgroundTasks,
    admin: Admin,
    common_db: Optional[Session] = None,
    tenant_id: Optional[str] = None,
) -> TraineeAdminOut:
    """Trainer/admin-side "register a new trainee" form - distinct from the
    trainee's own self-registration in services/trainee_service.py."""
    if getattr(admin, "role", None) == "admin" and common_db is not None:
        _reject_forged_scope(resolve_scope(common_db, admin, tenant_id), payload)

    phone_int = int(payload.primaryPhone)
    existing = trainee_repository.get_admin_registration_conflict(
        db, phone_int, payload.primaryEmail, payload.username, payload.traineeUid
    )
    if existing:
        raise bad_request("A trainee with this UID, phone, email or username already exists")

    trainee = Trainee(
        traineeUid=payload.traineeUid,
        name=payload.fullName,
        email=payload.primaryEmail,
        phone=phone_int,
        gender=payload.gender,
        designation=payload.designation,
        district=payload.district,
        state=payload.state,
        profilePhoto=payload.profilePhoto,
        zone=payload.zone,
        region=payload.region,
        company=payload.company,
        requestedBy=payload.requestedBy,
        trainerEmployeeId=payload.trainerId,
        trainerName=payload.trainerName,
        supervisorUid=payload.supervisorId,
        supervisorName=payload.supervisorName,
        supervisorDesignation=payload.supervisorDesignation,
        agencyId=payload.agencyId,
        dob=payload.dob,
        address=payload.address,
        altPhone=payload.altPhone,
        altEmail=payload.altEmail,
        joinedOn=payload.joinedOn,
        jobStatus=payload.jobStatus,
        jobCity=payload.jobCity,
        jobPincode=payload.jobPincode,
        resignedOn=payload.resignedOn,
        username=payload.username,
        password=hash_password(payload.password),
        updatedBy=admin.username,
        status="Pending",
    )
    trainee = trainee_repository.create(db, trainee)

    background_tasks.add_task(ws_manager.broadcast, tenant_id, {"type": "trainee_created", "traineeUid": trainee.traineeUid})

    log_activity(
        db,
        action="REGISTER_TRAINEE",
        username=admin.username,
        role=admin.role,
        remarks=f"Registered trainee {trainee.traineeUid} ({trainee.name})",
    )

    return _trainee_to_admin_out(trainee)


def list_trainees_admin(
    db: Session, admin: Admin, common_db: Optional[Session] = None, tenant_id: Optional[str] = None
) -> list[TraineeAdminOut]:
    """Powers both the admin Trainee List and a trainer's own "Trainee List" (their More menu -
    same endpoint, same response shape, scoped differently per caller). An admin-table account
    (role="admin") is scoped by their admin_access grant, exactly like the Training List and
    Attendance list (Trainee has its own company/zone/region columns, so no join is needed - see
    access_scope_conditions). A trainer (agency-team, or an admin-table account with
    role="trainer") is scoped to their own assigned/rostered trainees instead
    (trainee_repository.trainer_owned_condition) - unrelated to company/zone, the same as how
    their own trainings and attendance already work."""
    if getattr(admin, "role", None) == "admin":
        scope = (
            resolve_scope(common_db, admin, tenant_id)
            if common_db is not None
            else AccessScope.denied(tenant_id or "", "no scope context")
        )
        conditions = dashboard_repository.access_scope_conditions(scope, Trainee.company, Trainee.zone, Trainee.region)
    else:
        conditions = [trainee_repository.trainer_owned_condition(admin.username)]
    trainees = trainee_repository.list_scoped(db, conditions)
    return [_trainee_to_admin_out(t) for t in trainees]

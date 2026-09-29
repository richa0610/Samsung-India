from typing import Optional

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.core.security import hash_password
from app.models.admin import Admin
from app.models.trainee import Trainee
from app.repositories import dashboard_repository, trainee_repository
from app.routers.ws import manager as ws_manager
from app.schemas.trainee_admin import TraineeAdminIn, TraineeAdminOut, TraineePageResponse
from app.services import placement_rules
from app.services.access_service import resolve_scope
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
    # Company/zone/region and the assigned trainer come from the form but decide who can see and
    # manage this trainee, so they follow the same placement rule as a training: a trainer - own
    # company and a same-company trainer; an admin - inside their grant, with a trainer from a
    # company it covers.
    placement_rules.authorize_placement(
        db, common_db, admin, resolve_scope(common_db, admin, tenant_id), tenant_id,
        company=payload.company, zone=payload.zone, region=payload.region, trainer=payload.trainerId,
    )

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
    conditions = dashboard_repository.trainee_authorization_conditions(resolve_scope(common_db, admin, tenant_id))
    trainees = trainee_repository.list_scoped(db, conditions)
    return [_trainee_to_admin_out(t) for t in trainees]


def list_trainees_page(
    db: Session,
    admin: Admin,
    mode: str,
    search: Optional[str],
    sort: str,
    descending: bool,
    cursor: Optional[str],
    limit: int,
    page: Optional[int] = None,
    common_db: Optional[Session] = None,
    tenant_id: Optional[str] = None,
) -> TraineePageResponse:
    """One page of the Trainee List (or, with `mode="pending"`, the Pending Trainee List) - the
    same rows `list_trainees_admin` authorizes, but counted, searched, sorted and paged in SQL."""
    conditions = dashboard_repository.trainee_authorization_conditions(resolve_scope(common_db, admin, tenant_id))
    try:
        trainees, next_cursor, total = trainee_repository.list_page(
            db, conditions, mode, search, sort, descending, cursor, limit, page
        )
    except (ValueError, KeyError, TypeError):
        raise bad_request("Invalid page cursor")
    return TraineePageResponse(items=[_trainee_to_admin_out(t) for t in trainees], nextCursor=next_cursor, total=total)

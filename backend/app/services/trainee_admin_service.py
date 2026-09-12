from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from app.core.exceptions import bad_request
from app.core.security import hash_password
from app.models.admin import Admin
from app.models.trainee import Trainee
from app.repositories import trainee_repository
from app.routers.ws import manager as ws_manager
from app.schemas.trainee_admin import TraineeAdminIn, TraineeAdminOut
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
    db: Session, payload: TraineeAdminIn, background_tasks: BackgroundTasks, admin: Admin
) -> TraineeAdminOut:
    """Trainer/admin-side "register a new trainee" form - distinct from the
    trainee's own self-registration in services/trainee_service.py."""
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

    background_tasks.add_task(ws_manager.broadcast, {"type": "trainee_created", "traineeUid": trainee.traineeUid})

    return _trainee_to_admin_out(trainee)


def list_trainees_admin(db: Session) -> list[TraineeAdminOut]:
    trainees = trainee_repository.list_all(db)
    return [_trainee_to_admin_out(t) for t in trainees]

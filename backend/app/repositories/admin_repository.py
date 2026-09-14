from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.admin import Admin
from app.models.agency_team import AgencyTeam


def get_admin_by_username(db: Session, username: str) -> Admin | None:
    return db.query(Admin).filter(Admin.username == username).first()


def get_admin_by_username_and_role(db: Session, username: str, role: str) -> Admin | None:
    return db.query(Admin).filter(Admin.username == username, Admin.role == role).first()


def get_agency_by_username(db: Session, username: str) -> AgencyTeam | None:
    return db.query(AgencyTeam).filter(AgencyTeam.username == username).first()


def get_agency_by_username_or_offer_id(db: Session, identifier: str) -> AgencyTeam | None:
    return (
        db.query(AgencyTeam)
        .filter(or_(AgencyTeam.username == identifier, AgencyTeam.offerId == identifier))
        .first()
    )


def get_agency_by_username_and_role(db: Session, username: str, role: str) -> AgencyTeam | None:
    return db.query(AgencyTeam).filter(AgencyTeam.username == username, AgencyTeam.role == role).first()


def list_admin_trainers(db: Session) -> list[Admin]:
    return db.query(Admin).filter(Admin.role == "trainer").all()


def list_agency_trainers(db: Session, company: str | None = None) -> list[AgencyTeam]:
    query = db.query(AgencyTeam).filter(AgencyTeam.role == "trainer")
    if company:
        query = query.filter(func.lower(AgencyTeam.company) == company.strip().lower())
    return query.all()


def get_admins_by_usernames(db: Session, usernames: set[str]) -> list[Admin]:
    if not usernames:
        return []
    return db.query(Admin).filter(Admin.username.in_(usernames)).all()


def get_agents_by_usernames(db: Session, usernames: set[str]) -> list[AgencyTeam]:
    if not usernames:
        return []
    return db.query(AgencyTeam).filter(AgencyTeam.username.in_(usernames)).all()


def save(db: Session, entity: Admin | AgencyTeam) -> Admin | AgencyTeam:
    db.commit()
    db.refresh(entity)
    return entity

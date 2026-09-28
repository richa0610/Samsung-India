"""Database-side aggregates for the admin dashboard.

The dashboard used to load every conference / attendance / result row in the
tenant and count them in Python. Everything here is a filtered `COUNT` /
`GROUP BY` instead, so the work (and the data leaving the database) scales
with the result - a handful of grouped rows - not with how many trainings the
tenant has stored. The filter semantics mirror `ConferenceFilters.matches`
exactly: case-insensitive, whitespace-trimmed matches, string date bounds.

Round trips matter more than query cost here: the database is remote, so every
statement costs one network round trip (~40 ms) however little work it does.
`dashboard_snapshot` therefore sends every aggregate the dashboard needs as ONE
`UNION ALL` statement instead of eight separate ones.
"""

from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import String, and_, case, cast, exists, false, func, literal, null, or_, select, union_all
from sqlalchemy.orm import Session

from app.core.constants import PASS_THRESHOLD_PERCENT
from app.dependencies.filters import ConferenceFilters
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.services.access_service import AccessScope


def _norm(column):
    """SQL twin of the Python `(value or "").strip().lower()` used by filters."""
    return func.lower(func.trim(func.coalesce(column, "")))


def conference_conditions(filters: Optional[ConferenceFilters], include_cancelled: bool = False) -> list:
    """WHERE conditions for "a training that counts on the dashboard": not
    cancelled (unless `include_cancelled`, for lists that still show them), and
    inside the admin's filter / identity scope."""
    status = func.lower(Conference.conferenceStatus)
    conditions = [] if include_cancelled else [or_(Conference.conferenceStatus.is_(None), status != "cancelled")]
    if filters is None:
        return conditions

    # Plain column comparisons (no function wrapped around the column) so the
    # date index can be used. A missing date counts as "" like the Python
    # filter: excluded by a start bound, included by an end bound.
    if filters.start:
        conditions.append(Conference.conferenceDate >= filters.start)
    if filters.end:
        conditions.append(or_(Conference.conferenceDate.is_(None), Conference.conferenceDate <= filters.end))
    for column, values in (
        (Conference.trainerEmployeeId, filters.trainers),
        (Conference.zone, filters.zones),
        (Conference.region, filters.regions),
        (Conference.sessionType, filters.session_types),
        (Conference.trainingType, filters.training_types),
    ):
        if values:
            conditions.append(_norm(column).in_(values))
    if filters.company:
        conditions.append(_norm(Conference.company) == filters.company.strip().lower())
    return conditions


def access_scope_conditions(
    scope: AccessScope,
    company_column=Conference.company,
    zone_column=Conference.zone,
    region_column=Conference.region,
) -> list:
    """WHERE conditions equivalent to `scope.allows_row` (access_service) - the SQL twin of that
    per-row check, for a list query, the same relationship `_norm` above already has with
    `ConferenceFilters.matches`. Callers AND this with `conference_conditions` (and any other
    filter); never OR it in and never skip it - it is the authorization boundary, not a filter.

    Defaults to the `Conference` columns (the Training List, the Attendance list); pass
    `Trainee.company` / `.zone` / `.region` for a trainee list - same rule, same rules, a
    different table, because `Trainee` carries its own company/zone/region rather than being
    joined through a conference.

    A Super Admin's scope adds no condition (already vetted: resolve_scope only sets `is_super`
    from a real, active `super_admin` grant). Anything else narrows to the union of the rules the
    caller actually holds - a Company Admin's company, a Coordinator's company+zone, a
    Sub-coordinator's company+region. No allowed rule, or no access at all, both come out the
    same way: a condition that matches nothing, so a missing/denied/malformed grant can never
    fall through to "no restriction" (the fail-open bug this replaces)."""
    if not scope.allowed:
        return [false()]
    if scope.is_super:
        return []
    if not scope.rules:
        return [false()]

    def rule_condition(rule):
        condition = _norm(company_column) == rule.company
        if rule.zone is not None:
            condition = and_(condition, _norm(zone_column) == rule.zone)
        if rule.region is not None:
            condition = and_(condition, _norm(region_column) == rule.region)
        return condition

    return [or_(*(rule_condition(rule) for rule in scope.rules))]


def counted_condition():
    """A training the Training / Trainers cards count: Completed, or approved
    and still to run (Scheduled / Ongoing)."""
    status = func.lower(Conference.conferenceStatus)
    return or_(
        status == "completed",
        and_(func.lower(Conference.status) == "approved", status.in_(("scheduled", "ongoing"))),
    )


# ---------------------------------------------------------------------------
# One statement for everything
#
# Every member of the UNION ALL has the same shape - (kind, a, b, c, n1, n2, n3) -
# so the different aggregates can share one result set. `kind` says which
# aggregate a row belongs to; unused columns are NULL. Text values are cast to
# strings and numbers left as numbers so the database can unify each column.
# ---------------------------------------------------------------------------


def _text(column):
    return cast(column, String)


def _member(kind: str, a=None, b=None, c=None, n1=None, n2=None, n3=None) -> list:
    values = {"a": a, "b": b, "c": c, "n1": n1, "n2": n2, "n3": n3}
    return [literal(kind).label("k")] + [
        (value if value is not None else null()).label(name) for name, value in values.items()
    ]


def _count_of(query):
    """Scalar sub-select: how many rows `query` returns."""
    return select(func.count()).select_from(query.subquery()).scalar_subquery()


@dataclass
class DashboardSnapshot:
    # (trainingType, conferenceStatus, approval status, count), in the order each
    # group's first row was created.
    status_groups: list[tuple] = field(default_factory=list)
    # (trainingType, confirmedPax, count)
    pax_groups: list[tuple] = field(default_factory=list)
    # (trainingType, attendance status, sessionMeta, count)
    attendance_groups: list[tuple] = field(default_factory=list)
    busy_trainers: set = field(default_factory=set)
    agency_trainers: set = field(default_factory=set)
    attempts: int = 0
    passed: int = 0
    percent_total: float = 0.0
    present_pairs: int = 0
    missed_pairs: int = 0
    submitted_pairs: int = 0


def dashboard_snapshot(db: Session, conditions: list, agency_company: Optional[str] = None) -> DashboardSnapshot:
    """Everything the admin dashboard counts, in a single round trip.

    `conditions` = the in-scope trainings (see `conference_conditions`).
    `agency_company` narrows the partner-agency trainer pool the same way the
    dashboard's trainer pool is narrowed."""
    join_conf_att = Conference.conferenceUid == Attendance.conferenceUid
    join_conf_res = Conference.conferenceUid == AssessmentResult.conferenceUid

    status_q = (
        select(
            *_member(
                "status",
                _text(Conference.trainingType),
                _text(Conference.conferenceStatus),
                _text(Conference.status),
                n1=func.count(),
                n2=func.min(Conference.id),
            )
        )
        .where(*conditions)
        .group_by(Conference.trainingType, Conference.conferenceStatus, Conference.status)
    )
    pax_q = (
        select(*_member("pax", _text(Conference.trainingType), _text(Conference.confirmedPax), n1=func.count()))
        .where(*conditions)
        .group_by(Conference.trainingType, Conference.confirmedPax)
    )
    attendance_q = (
        select(
            *_member(
                "att",
                _text(Conference.trainingType),
                _text(Attendance.status),
                _text(Attendance.sessionMeta),
                n1=func.count(),
            )
        )
        .select_from(Attendance)
        .join(Conference, join_conf_att)
        .where(*conditions)
        .group_by(Conference.trainingType, Attendance.status, Attendance.sessionMeta)
    )
    busy_q = (
        select(*_member("busy", _text(Conference.trainerEmployeeId)))
        .where(*conditions, counted_condition())
        .distinct()
    )
    agency_conditions = [AgencyTeam.role == "trainer"]
    if agency_company:
        agency_conditions.append(func.lower(AgencyTeam.company) == agency_company.strip().lower())
    agency_q = select(*_member("agency", _text(AgencyTeam.username))).where(*agency_conditions)

    results_q = (
        select(
            *_member(
                "res",
                n1=func.count(),
                n2=func.coalesce(func.sum(case((AssessmentResult.percentage >= PASS_THRESHOLD_PERCENT, 1), else_=0)), 0),
                n3=func.coalesce(func.sum(AssessmentResult.percentage), 0),
            )
        )
        .select_from(AssessmentResult)
        .join(Conference, join_conf_res)
        .where(AssessmentResult.status == "Submitted", *conditions)
    )

    # Present (training, trainee) pairs, and how many of them never submitted
    # anything; plus every pair that did submit.
    present_pairs = (
        select(Attendance.conferenceUid, Attendance.traineeUid)
        .join(Conference, join_conf_att)
        .where(Attendance.status == "Present", *conditions)
        .distinct()
    )
    submitted = exists().where(
        AssessmentResult.status == "Submitted",
        AssessmentResult.conferenceUid == Attendance.conferenceUid,
        AssessmentResult.traineeUid == Attendance.traineeUid,
    )
    submitted_pairs = (
        select(AssessmentResult.conferenceUid, AssessmentResult.traineeUid)
        .join(Conference, join_conf_res)
        .where(
            AssessmentResult.status == "Submitted",
            AssessmentResult.conferenceUid != "",
            AssessmentResult.traineeUid != "",
            *conditions,
        )
        .distinct()
    )
    pairs_q = select(
        *_member(
            "pairs",
            n1=_count_of(present_pairs),
            n2=_count_of(present_pairs.where(~submitted)),
            n3=_count_of(submitted_pairs),
        )
    )

    rows = db.execute(union_all(status_q, pax_q, attendance_q, busy_q, agency_q, results_q, pairs_q)).all()

    snapshot = DashboardSnapshot()
    ordered_status: list[tuple] = []
    for kind, a, b, c, n1, n2, n3 in rows:
        if kind == "status":
            ordered_status.append((int(n2 or 0), a, b, c, int(n1)))
        elif kind == "pax":
            snapshot.pax_groups.append((a, b, int(n1)))
        elif kind == "att":
            snapshot.attendance_groups.append((a, b, c, int(n1)))
        elif kind == "busy":
            if a:
                snapshot.busy_trainers.add(a)
        elif kind == "agency":
            if a:
                snapshot.agency_trainers.add(a)
        elif kind == "res":
            snapshot.attempts = int(n1 or 0)
            snapshot.passed = int(n2 or 0)
            snapshot.percent_total = float(n3 or 0)
        elif kind == "pairs":
            snapshot.present_pairs = int(n1 or 0)
            snapshot.missed_pairs = int(n2 or 0)
            snapshot.submitted_pairs = int(n3 or 0)
    ordered_status.sort(key=lambda row: row[0])
    snapshot.status_groups = [row[1:] for row in ordered_status]
    return snapshot

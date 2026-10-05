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
from typing import Collection, Optional

from sqlalchemy import (
    Boolean, Float, String, and_, case, cast, exists, false, func, literal, literal_column, not_, null, or_, select, true,
    tuple_, type_coerce, union, union_all,
)
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import ColumnElement

from app.core.constants import PASS_THRESHOLD_PERCENT
from app.dependencies.filters import ConferenceFilters
from app.models.agency_team import AgencyTeam
from app.models.attendance import Attendance
from app.models.conference import Conference
from app.models.quiz import AssessmentResult
from app.models.trainee import Trainee
from app.repositories import conference_repository, trainee_repository
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


def conference_authorization_conditions(scope: AccessScope) -> list:
    """WHERE conditions for the conferences `scope` may operate: an admin-panel grant by
    company/zone/region (`access_scope_conditions`), an active trainer by assignment
    (`conference_repository.trainer_condition`). Anything else matches nothing. AND these with
    any other filter or search - never OR them in."""
    if scope.is_admin_panel:
        return access_scope_conditions(scope)
    if scope.is_trainer:
        return [conference_repository.trainer_condition(scope.trainer_username)]
    return [false()]


def trainee_authorization_conditions(scope: AccessScope, *, listing: bool = False) -> list:
    """The trainee-table twin of `conference_authorization_conditions`: an admin-panel grant by
    the trainee's own company/zone/region, an active trainer by assignment or roster
    (`trainee_repository.trainer_owned_condition`). Anything else matches nothing. `listing=True`
    gives the same set in the form that is fast for listing / counting many rows (the Trainee
    List); leave it off when checking one known trainee."""
    if scope.is_admin_panel:
        return access_scope_conditions(scope, Trainee.company, Trainee.zone, Trainee.region)
    if scope.is_trainer:
        owned = trainee_repository.trainer_owned_list_condition if listing else trainee_repository.trainer_owned_condition
        return [owned(scope.trainer_username)]
    return [false()]


def trainer_summary_counts(
    db: Session, trainer_username: str, start: Optional[str], end: Optional[str], today: str, today_ist: str
) -> dict:
    """The trainer Home dashboard's numbers, counted in SQL (two statements) instead of loading the
    trainer's trainings into Python. Same definitions as before (tests/_legacy_trainer_agenda.py
    is the reference they're proven equal to):

      listed        today's trainings (no range given - the default view), else those in start..end
      totalSessions listed, not cancelled                     completed  ... of those, Completed
      pending       approved, not yet started / finished, not past - across ALL the trainer's
                    trainings on the default view, else across the counted range
      missed        approved, never started, date already past - within the counted range
      ongoing       running now (Ongoing / Live) - all trainings on the default view, else the range
      totalTrainees distinct trainees marked Present or with a submitted test - every training on
                    the default view, else the listed ones"""
    owned = conference_repository.trainer_condition(trainer_username)
    default_view = start is None and end is None
    date_bounds = [Conference.conferenceDate == today] if default_view else [
        condition for condition in (
            Conference.conferenceDate >= start if start else None,
            Conference.conferenceDate <= end if end else None,
        ) if condition is not None
    ]
    listed = and_(*date_bounds) if date_bounds else true()

    status = func.lower(func.coalesce(Conference.conferenceStatus, ""))
    approval = func.lower(func.coalesce(Conference.status, ""))
    counted = and_(listed, status != "cancelled")
    not_started_approved = and_(approval == "approved", status.notin_(("ongoing", "live", "completed", "cancelled")))
    past = and_(func.coalesce(Conference.conferenceDate, "") != "", Conference.conferenceDate < today_ist)
    scoped = true() if default_view else counted

    def how_many(condition):
        return func.coalesce(func.sum(case((condition, 1), else_=0)), 0)

    total, completed, pending, missed, ongoing = db.execute(
        select(
            how_many(counted),
            how_many(and_(counted, status == "completed")),
            how_many(and_(scoped, not_started_approved, not_(past))),
            how_many(and_(counted, not_started_approved, past)),
            how_many(and_(scoped, status.in_(("ongoing", "live")))),
        ).where(owned)
    ).one()

    trainings = select(Conference.conferenceUid).where(owned, *([] if default_view else [listed]))
    trained = union(
        select(Attendance.traineeUid).where(Attendance.conferenceUid.in_(trainings), Attendance.status == "Present"),
        select(AssessmentResult.traineeUid).where(AssessmentResult.conferenceUid.in_(trainings), AssessmentResult.status == "Submitted"),
    ).subquery()
    total_trainees = db.scalar(select(func.count()).select_from(trained)) or 0

    return {
        "totalTrainees": int(total_trainees),
        "totalSessions": int(total),
        "completed": int(completed),
        "pending": int(pending),
        "missed": int(missed),
        "ongoing": int(ongoing),
    }


def count_trained_by_conference(db: Session, conference_uids: Collection[str]) -> dict[str, int]:
    """{conferenceUid: real headcount} - the distinct trainees marked Present or with a submitted
    test there (the same definition as the session dashboard), counted in SQL: one grouped row per
    training comes back, never one row per trainee. Trainings with nobody are left out (0)."""
    if not conference_uids:
        return {}
    uids = sorted(set(conference_uids))
    trained = union(
        select(Attendance.conferenceUid.label("conferenceUid"), Attendance.traineeUid.label("traineeUid"))
        .where(Attendance.conferenceUid.in_(uids), Attendance.status == "Present"),
        select(AssessmentResult.conferenceUid, AssessmentResult.traineeUid)
        .where(AssessmentResult.conferenceUid.in_(uids), AssessmentResult.status == "Submitted"),
    ).subquery()
    rows = db.execute(select(trained.c.conferenceUid, func.count()).group_by(trained.c.conferenceUid)).all()
    return {conference_uid: int(count) for conference_uid, count in rows}


# ---------------------------------------------------------------------------
# Trainee ranking - computed entirely in SQL, per request (never cached)
# ---------------------------------------------------------------------------

_LIVE_QUIZ_PATH = "$.liveQuiz.assessmentSuiteUid"


class live_quiz_suite_is(ColumnElement):
    """SQL for `module_flow.live_quiz_suite_uid(conference) == suite`: the Live Quiz test id stored
    in `sessionConfig` JSON equals `suite`. A missing, empty or malformed config, a missing key, or
    a non-text value (a number, null) never matches - as the Python lookup (json.loads + .get)
    behaves. Compiled per database below."""

    type = Boolean()
    inherit_cache = True

    def __init__(self, config, suite):
        self.config = config
        self.suite = suite


@compiles(live_quiz_suite_is)
def _live_quiz_suite_is_sqlite(element, compiler, **kw):
    config, suite = compiler.process(element.config, **kw), compiler.process(element.suite, **kw)
    # CASE guards the JSON functions: SQLite raises on malformed JSON, and CASE is evaluated lazily.
    return (
        f"(CASE WHEN json_valid({config}) THEN "
        f"(json_type({config}, '{_LIVE_QUIZ_PATH}') = 'text' AND json_extract({config}, '{_LIVE_QUIZ_PATH}') = {suite}) "
        f"ELSE 0 END)"
    )


@compiles(live_quiz_suite_is, "mysql")
def _live_quiz_suite_is_mysql(element, compiler, **kw):
    config, suite = compiler.process(element.config, **kw), compiler.process(element.suite, **kw)
    # Compared as JSON to JSON (a JSON string equals only that same string), so the column's
    # character set / collation never meets the JSON's - no "illegal mix of collations" - and a
    # JSON number or null never equals a text id.
    return (
        f"(CASE WHEN JSON_VALID({config}) THEN "
        f"COALESCE(JSON_EXTRACT({config}, '{_LIVE_QUIZ_PATH}') = CAST(JSON_QUOTE({suite}) AS JSON), 0) "
        f"ELSE 0 END)"
    )


def _counted_marks(trainee_uid: Optional[str] = None):
    """Per trainee: the summed Standard Test + Live Quiz marks (total, max) of Submitted results, at
    trainings that weren't cancelled, where the trainee was marked Present."""
    present = exists().where(
        Attendance.conferenceUid == AssessmentResult.conferenceUid,
        Attendance.traineeUid == AssessmentResult.traineeUid,
        Attendance.status == "Present",
    )
    counted_suite = or_(
        AssessmentResult.assessmentSuiteUid == Conference.postAssessmentUid,
        live_quiz_suite_is(Conference.sessionConfig, AssessmentResult.assessmentSuiteUid),
    )
    query = (
        select(
            AssessmentResult.traineeUid.label("traineeUid"),
            func.sum(AssessmentResult.totalScore).label("score"),
            func.sum(AssessmentResult.maxScore).label("maximum"),
        )
        .join(Conference, Conference.conferenceUid == AssessmentResult.conferenceUid)
        .where(
            AssessmentResult.status == "Submitted",
            func.lower(func.coalesce(Conference.conferenceStatus, "")) != "cancelled",
            present,
            counted_suite,
        )
        .group_by(AssessmentResult.traineeUid)
    )
    if trainee_uid is not None:
        query = query.where(AssessmentResult.traineeUid == trainee_uid)
    return query.subquery()


def _ranked(trainee_uid: Optional[str] = None):
    """Every ranked trainee - marked Present at least once - with their state and percent over
    those marks (0 with none). The percent is computed as a double (`* 1.0E0`) by the same
    expression for everyone, so equal marks always give equal percents."""
    population = select(Attendance.traineeUid.label("traineeUid")).where(Attendance.status == "Present")
    if trainee_uid is not None:
        population = population.where(Attendance.traineeUid == trainee_uid)
    population = population.distinct().subquery()
    marks = _counted_marks(trainee_uid)
    maximum = func.coalesce(marks.c.maximum, 0)
    # Typed as Float (no SQL cast): the percent comes back - and is bound back into the rank
    # comparison - as a plain float, never a Decimal the driver might send as text.
    percent = type_coerce(
        case(
            (maximum > 0, marks.c.score * literal_column("1.0E0") / marks.c.maximum * 100),
            else_=literal_column("0.0E0"),
        ),
        Float(),
    )
    return (
        select(population.c.traineeUid, Trainee.state.label("state"), percent.label("percent"))
        .select_from(population)
        .outerjoin(marks, marks.c.traineeUid == population.c.traineeUid)
        .outerjoin(Trainee, Trainee.traineeUid == population.c.traineeUid)
        .subquery()
    )


@dataclass(frozen=True)
class RankPosition:
    rank: Optional[int]
    total: int

    @property
    def percentile(self) -> Optional[float]:
        return round(self.rank / self.total * 100, 1) if self.rank is not None and self.total else None


def trainee_rank(db: Session, trainee_uid: str, state: Optional[str]) -> tuple[RankPosition, RankPosition]:
    """(global, state) competition rank of one trainee among every ranked trainee of this tenant:
    1 + how many have a strictly higher percent (ties share a rank). Never Present -> not ranked
    (rank None). No state -> an empty state pool. Two statements, aggregated in the database: no
    other trainee's row leaves it."""
    mine = db.execute(select(_ranked(trainee_uid).c.percent)).scalar_one_or_none()
    ranked = _ranked()
    in_state = ranked.c.state == state if state else false()
    higher = ranked.c.percent > mine if mine is not None else false()

    def how_many(condition):
        return func.coalesce(func.sum(case((condition, 1), else_=0)), 0)

    total, above, state_total, state_above = db.execute(
        select(func.count(), how_many(higher), how_many(in_state), how_many(and_(in_state, higher))).select_from(ranked)
    ).one()
    ranked_here = mine is not None
    return (
        RankPosition(1 + int(above) if ranked_here else None, int(total)),
        RankPosition(1 + int(state_above) if ranked_here and state else None, int(state_total)),
    )


def session_ranks(db: Session, trainee_uid: str, suite_by_conference: dict[str, str]) -> dict[str, int]:
    """{conferenceUid: the trainee's rank in that training's test} for the given (training, test)
    pairs, in ONE statement. Each trainee counts once, by their latest Submitted attempt (as the
    session dashboard's Top Performers does); rank = 1 + how many trainees scored strictly higher,
    so equal scores share a rank. Trainings where this trainee has no Submitted attempt are left out."""
    if not suite_by_conference:
        return {}
    pairs = sorted(suite_by_conference.items())

    def latest_attempts(name: str, only_trainee: Optional[str] = None):
        # Built separately for each use: one expanding IN list can't be shared by two aliases.
        result, newer = AssessmentResult.__table__.alias(f"{name}_result"), AssessmentResult.__table__.alias(f"{name}_newer")
        attempt, newer_attempt = func.coalesce(result.c.attemptNumber, 0), func.coalesce(newer.c.attemptNumber, 0)
        query = select(result.c.conferenceUid, result.c.traineeUid, result.c.percentage).where(
            tuple_(result.c.conferenceUid, result.c.assessmentSuiteUid).in_(pairs),
            result.c.status == "Submitted",
            ~exists().where(
                newer.c.conferenceUid == result.c.conferenceUid,
                newer.c.assessmentSuiteUid == result.c.assessmentSuiteUid,
                newer.c.traineeUid == result.c.traineeUid,
                newer.c.status == "Submitted",
                or_(newer_attempt > attempt, and_(newer_attempt == attempt, newer.c.id > result.c.id)),
            ),
        )
        if only_trainee is not None:
            query = query.where(result.c.traineeUid == only_trainee)
        return query.subquery(name)

    mine, others = latest_attempts("mine", trainee_uid), latest_attempts("others")
    rows = db.execute(
        select(mine.c.conferenceUid, func.count(others.c.traineeUid))
        .select_from(mine)
        .outerjoin(others, and_(others.c.conferenceUid == mine.c.conferenceUid, others.c.percentage > mine.c.percentage))
        .where(mine.c.traineeUid == trainee_uid)
        .group_by(mine.c.conferenceUid)
    ).all()
    return {conference_uid: 1 + int(higher) for conference_uid, higher in rows}


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


def dashboard_snapshot(
    db: Session, conditions: list, agency_companies: Optional[Collection[str]] = None
) -> DashboardSnapshot:
    """Everything the admin dashboard counts, in a single round trip.

    `conditions` = the in-scope trainings (see `conference_conditions`).
    `agency_companies` narrows the partner-agency trainer pool to those companies (normalized like
    every scope comparison); None = every company in this tenant, an empty set = none."""
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
    if agency_companies is not None:
        agency_conditions.append(_norm(AgencyTeam.company).in_(sorted(agency_companies)))
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

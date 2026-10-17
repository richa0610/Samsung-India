"""Brings the answers and results already in a tenant's database in line with the other system's
format - the rules new rows follow since 2026-10-16 (user):

  - option NUMBERS (app/services/answer_numbers.py): `questions.correct_answer` and the Standard Test /
    Live Quiz answers in `assessment.selectedOption` become the option's position in the question's
    option list, 1 = the first option shown. Survey answers are left as they are (not numbered).
  - "Completed": a finished result this app saved as "Submitted" (`assessment_results.status`) gets
    the other system's word.

    cd backend
    venv/Scripts/python.exe scripts/align_assessment_records.py                  # preview - writes nothing
    venv/Scripts/python.exe scripts/align_assessment_records.py --apply          # convert
    venv/Scripts/python.exe scripts/align_assessment_records.py --undo backups/align-assessment-<...>.json

Only a value that is an option's own id ("B", "very_good") is numbered. A value that is already a
number is left alone - on most questions an option's number and its id are the same ("2" is the second
of "1".."4") - so running it again changes nothing. Reported, never changed:
  - a number on a question whose option ids are numbers in another order (e.g. "1", "3", "4" after an
    option was removed in the builder): whether an old answer meant the id or the position can't be told;
  - a value that names none of its question's options, and an answer whose question or training is gone.

What --apply changes (each row's old and new value) is saved to backups/ before it is committed; --undo
puts back exactly those values, on rows that still hold what this script wrote.

Run it only once the backend that reads numbers and "Completed" is live everywhere it serves this
database (Render and any local server): an older backend would compare numbered answers with letters,
and wouldn't count a "Completed" result at all.
"""

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app.models  # noqa: E402,F401 - registers every table
from app.core.config import settings  # noqa: E402
from app.core.constants import RESULT_COMPLETED, RESULT_SUBMITTED_BEFORE  # noqa: E402
from app.models.conference import Conference  # noqa: E402
from app.models.quiz import Assessment, AssessmentResult, Question  # noqa: E402
from app.services import answer_numbers  # noqa: E402
from app.services.module_flow import live_quiz_suite_uid  # noqa: E402

BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"
# Each table this script changes -> (model, the column it changes there).
COLUMNS = {
    "questions": (Question, Question.correct_answer),
    "assessment": (Assessment, Assessment.selectedOption),
    "assessment_results": (AssessmentResult, AssessmentResult.status),
}
_BATCH = 500  # ids per UPDATE


@dataclass(frozen=True)
class Change:
    table: str
    row_id: int
    old: str
    new: str


@dataclass
class Plan:
    changes: list[Change] = field(default_factory=list)
    left: Counter = field(default_factory=Counter)  # why a value stays as it is -> how many
    problems: list[str] = field(default_factory=list)  # reported, never changed


def _ids_out_of_order(ids: list[str]) -> bool:
    """Option ids that are numbers but not 1, 2, 3, ... in the order shown (e.g. "1", "3", "4")."""
    return any(i.isdigit() for i in ids) and ids != [str(n) for n in range(1, len(ids) + 1)]


def _check(plan: Plan, table: str, row_id: int, question: Question, saved: Optional[str], what: str) -> None:
    """One saved value: a change to make, or why it stays."""
    value = (saved or "").strip()
    if not value:
        plan.left["empty"] += 1
        return
    ids = answer_numbers.option_ids(question)
    if not ids:
        plan.left["question has no readable options"] += 1
    elif value.isdigit() and _ids_out_of_order(ids):
        plan.problems.append(f"{what} = {value!r}: question {question.id}'s option ids are {', '.join(ids)} - id or position?")
    elif value.isdigit():
        if answer_numbers.position(question, value) is None:
            plan.problems.append(f"{what} = {value!r}: question {question.id} has only {len(ids)} option(s)")
        else:
            plan.left["already a number"] += 1
    elif value in ids:
        plan.changes.append(Change(table, row_id, saved, str(ids.index(value) + 1)))
    else:
        plan.problems.append(f"{what} = {value!r}: not one of question {question.id}'s options ({', '.join(ids)})")


def _numbered_suites(conference: Conference) -> set[str]:
    """The question sets whose answers are numbered in this training: its Standard Test and Live Quiz -
    the module a submission counts as (trainee_access.module_of_suite tries the Standard Test first)."""
    return {suite for suite in (conference.postAssessmentUid, live_quiz_suite_uid(conference)) if suite}


def make_plan(db: Session) -> Plan:
    plan = Plan()
    questions = {q.id: q for q in db.query(Question).order_by(Question.id)}
    for question in questions.values():
        _check(plan, "questions", question.id, question, question.correct_answer, f"question {question.id} answer key")

    answers = db.query(Assessment).filter(Assessment.selectedOption.isnot(None)).order_by(Assessment.id).all()
    conference_uids = {a.conferenceUid for a in answers}
    conferences = {c.conferenceUid: c for c in db.query(Conference).filter(Conference.conferenceUid.in_(conference_uids))}
    for answer in answers:
        what = f"answer {answer.id}"
        conference = conferences.get(answer.conferenceUid)
        question = questions.get(int(answer.questionId)) if (answer.questionId or "").isdigit() else None
        if conference is None or question is None:
            plan.problems.append(f"{what}: its {'training' if conference is None else 'question'} is not in this database")
        elif answer.assessmentSuiteUid in _numbered_suites(conference):
            _check(plan, "assessment", answer.id, question, answer.selectedOption, what)
        elif answer.assessmentSuiteUid == conference.surveyUid:
            plan.left["survey answer"] += 1
        else:
            plan.problems.append(f"{what}: question set {answer.assessmentSuiteUid} isn't a module of {answer.conferenceUid}")

    submitted = db.query(AssessmentResult.id).filter(AssessmentResult.status == RESULT_SUBMITTED_BEFORE).order_by(AssessmentResult.id)
    plan.changes += [Change("assessment_results", result_id, RESULT_SUBMITTED_BEFORE, RESULT_COMPLETED) for (result_id,) in submitted]
    return plan


def _rewrite(db: Session, table: str, groups: dict[tuple[str, str], list[int]]) -> int:
    """Sets each group's rows from one value to another - only rows still holding the first value."""
    model, column = COLUMNS[table]
    done = 0
    for (current, value), row_ids in groups.items():
        for start in range(0, len(row_ids), _BATCH):
            done += (
                db.query(model)
                .filter(model.id.in_(row_ids[start:start + _BATCH]), column == current)
                .update({column: value}, synchronize_session=False)
            )
    return done


def _grouped(changes: list[Change], *, reverse: bool = False) -> dict[str, dict[tuple[str, str], list[int]]]:
    """{table: {(value now, value to write): row ids}} - a handful of UPDATEs instead of one per row."""
    groups: dict[str, dict[tuple[str, str], list[int]]] = defaultdict(lambda: defaultdict(list))
    for change in changes:
        key = (change.new, change.old) if reverse else (change.old, change.new)
        groups[change.table][key].append(change.row_id)
    return groups


def apply(db: Session, plan: Plan, tenant: str) -> tuple[int, Path]:
    """Converts the planned values, saving every change to backups/ before committing."""
    BACKUP_DIR.mkdir(exist_ok=True)
    backup = BACKUP_DIR / f"align-assessment-{tenant}-{datetime.now():%Y%m%d-%H%M%S}.json"
    backup.write_text(json.dumps({"tenant": tenant, "changes": [asdict(c) for c in plan.changes]}, indent=2), encoding="utf-8")
    done = sum(_rewrite(db, table, groups) for table, groups in _grouped(plan.changes).items())
    db.commit()
    return done, backup


def undo(db: Session, backup: Path, tenant: str) -> tuple[int, int]:
    """Puts back the values a backup lists, on rows still holding what the script wrote. Returns
    (restored, left alone because they changed since)."""
    saved = json.loads(backup.read_text(encoding="utf-8"))
    if saved.get("tenant") != tenant:
        raise SystemExit(f"{backup.name} is for tenant {saved.get('tenant')!r}, not {tenant!r} - nothing changed.")
    changes = [Change(**c) for c in saved["changes"]]
    restored = sum(_rewrite(db, table, groups) for table, groups in _grouped(changes, reverse=True).items())
    db.commit()
    return restored, len(changes) - restored


def report(plan: Plan) -> None:
    for table in COLUMNS:
        moves = Counter((c.old, c.new) for c in plan.changes if c.table == table)
        print(f"{table}: {sum(moves.values())} value(s) to change")
        for (old, new), count in sorted(moves.items()):
            print(f"    {old!r} -> {new!r}: {count}")
    for reason, count in sorted(plan.left.items()):
        print(f"left as is ({reason}): {count}")
    if plan.problems:
        print(f"\nReported, not changed ({len(plan.problems)}):")
        for problem in plan.problems[:50]:
            print(f"    {problem}")
        if len(plan.problems) > 50:
            print(f"    ... and {len(plan.problems) - 50} more")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--apply", action="store_true", help="make the changes (default: preview only)")
    parser.add_argument("--undo", type=Path, metavar="BACKUP", help="put back exactly what a backup lists")
    parser.add_argument("--tenant", default=settings.DEFAULT_TENANT_ID)
    args = parser.parse_args()
    if args.apply and args.undo:
        parser.error("give --apply or --undo, not both")

    from scripts._tenant_db import tenant_engine  # local: needs the app's settings, never the test ones

    db = sessionmaker(bind=tenant_engine(args.tenant))()
    try:
        if args.undo:
            restored, left = undo(db, args.undo, args.tenant)
            print(f"Put back {restored} value(s) from {args.undo.name}." + (f" {left} had changed since and were left." if left else ""))
            return
        plan = make_plan(db)
        report(plan)
        if not args.apply:
            print(f"\nPreview only: {len(plan.changes)} value(s) would change. Run again with --apply to change them.")
        elif plan.changes:
            done, backup = apply(db, plan, args.tenant)
            print(f"\nChanged {done} value(s). Undo file: {backup}")
        else:
            print("\nNothing to change - everything is already in the new format.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

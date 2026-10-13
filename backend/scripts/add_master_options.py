"""Adds dropdown options to the master list from a JSON file, so no option is ever written into
code: each category (found by name - any letter case or spacing - and created, Approved, when it
doesn't exist yet) and its options (approved `subcategory` rows):

    {"categories": [
        {"name": "Audience", "visibleOnWeb": "Conference", "options": ["SEC", "OT SEC", ...]},
        {"name": "North", "visibleOnWeb": "Zone", "options": ["North 1", ...]}
    ]}

    cd backend
    venv/Scripts/python.exe scripts/add_master_options.py scripts/master_options.samsung.json          # preview - writes nothing
    venv/Scripts/python.exe scripts/add_master_options.py scripts/master_options.samsung.json --apply  # add what's missing
    venv/Scripts/python.exe scripts/add_master_options.py --undo backups/master-options-<...>.json      # remove exactly that

An option the category already has (same name, any spelling, any status) is reported and left
alone, never duplicated or changed. A category that exists but isn't Approved, is there twice, or
is marked differently (`visibleOnWeb`) stops the run before anything is written. What --apply adds
is saved to backups/ before it is committed, so --undo removes exactly those rows and nothing else.
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import app.models  # noqa: E402,F401 - registers every table and its UID hooks (categoryUid, subCategoryUid)
from app.core.config import settings  # noqa: E402
from app.models.category import Category, SubCategory  # noqa: E402

ADDED_BY = "system:admin-data-fix"
APPROVED = "Approved"
NOT_MARKED = "No"  # the `visibleOnWeb` column's own default
BACKUP_DIR = Path(__file__).resolve().parent.parent / "backups"


def _clean(name: str) -> str:
    return " ".join(name.split())


def _key(name: Optional[str]) -> str:
    """How two spellings of one name compare: inner spacing collapsed, any letter case."""
    return _clean(name or "").lower()


@dataclass
class Step:
    """One category of the file: whether it must be created, and which options it lacks."""

    name: str
    visible_on_web: str
    category_uid: Optional[str] = None  # None: the category is created
    options: list[str] = field(default_factory=list)


def load_plan(path: Path) -> list[tuple[str, str, list[str]]]:
    """(category name, its visibleOnWeb mark, option names) per category in the file - trimmed,
    blanks dropped, each name once."""
    plan = []
    for entry in json.loads(path.read_text(encoding="utf-8"))["categories"]:
        names: dict[str, str] = {}
        for name in entry["options"]:
            if name and name.strip():
                names.setdefault(_key(name), _clean(name))
        plan.append((_clean(entry["name"]), _clean(entry.get("visibleOnWeb") or NOT_MARKED), list(names.values())))
    return plan


def preview(db: Session, plan: list[tuple[str, str, list[str]]]) -> tuple[list[Step], list[str]]:
    """Prints what each category has and what it would get, and returns the steps --apply would
    take plus anything that stops the run."""
    categories = db.query(Category).all()
    steps: list[Step] = []
    problems: list[str] = []
    for name, mark, options in plan:
        matches = [c for c in categories if _key(c.name) == _key(name)]
        if len(matches) > 1:
            problems.append(f"category {name!r} is in the database {len(matches)} times")
            continue
        category = matches[0] if matches else None
        if category is not None and category.status != APPROVED:
            problems.append(f"category {name!r} exists but is {category.status}, not Approved")
            continue
        if category is not None and _key(category.visibleOnWeb or NOT_MARKED) != _key(mark):
            problems.append(f"category {name!r} is marked {category.visibleOnWeb!r}, not {mark!r}")
            continue
        step = Step(name, mark, category.categoryUid if category else None)
        existing = {}
        if category is not None:
            existing = {_key(r.subCategory): r for r in db.query(SubCategory).filter(SubCategory.categoryUid == category.categoryUid)}
        print(f"\n{name}  " + (f"(exists, {category.categoryUid})" if category else f"(CREATE category, marked {mark!r})"))
        for option in options:
            row = existing.get(_key(option))
            if row is None:
                step.options.append(option)
                print(f"  ADD     {option}")
            else:
                print(f"  exists  {row.subCategory}  [{row.status}, {row.subCategoryUid}]")
        wanted = {_key(option) for option in options}
        for key, row in existing.items():
            if key not in wanted:
                print(f"  (in the database, not in the file)  {row.subCategory}  [{row.status}]")
        steps.append(step)
    return steps, problems


def apply(db: Session, steps: list[Step], tenant: str) -> Path:
    """Creates the missing categories and adds the missing options, all Approved, and saves what
    it added to backups/ before committing."""
    remark = f"Added by an admin data fix on {datetime.now():%Y-%m-%d} (Add Training dropdown options)"
    created: list[Category] = []
    for step in steps:
        if step.category_uid is None:
            category = Category(name=step.name, visibleOnWeb=step.visible_on_web, status=APPROVED, updatedBy=ADDED_BY, remarks=remark)
            db.add(category)
            db.flush()  # the UID hook gives it its categoryUid
            created.append(category)
            step.category_uid = category.categoryUid
    added = [
        SubCategory(categoryUid=step.category_uid, subCategory=option, status=APPROVED, updatedBy=ADDED_BY, remarks=remark)
        for step in steps
        for option in step.options
    ]
    db.add_all(added)
    db.flush()  # ... and each option its subCategoryUid
    BACKUP_DIR.mkdir(exist_ok=True)
    backup = BACKUP_DIR / f"master-options-{tenant}-{datetime.now():%Y%m%d-%H%M%S}.json"
    backup.write_text(json.dumps({
        "tenant": tenant,
        "categories": [c.categoryUid for c in created],
        "subcategories": [s.subCategoryUid for s in added],
    }, indent=2), encoding="utf-8")
    db.commit()
    return backup


def undo(db: Session, backup: Path, tenant: str) -> tuple[int, int, list[str]]:
    """Removes exactly the rows a backup lists, and only those this script added: its options,
    then its categories - except one that has gained an option since (that one is kept)."""
    saved = json.loads(backup.read_text(encoding="utf-8"))
    if saved.get("tenant") != tenant:
        raise SystemExit(f"{backup.name} is for tenant {saved.get('tenant')!r}, not {tenant!r} - nothing removed.")
    options = (
        db.query(SubCategory)
        .filter(SubCategory.subCategoryUid.in_(saved["subcategories"]), SubCategory.updatedBy == ADDED_BY)
        .delete(synchronize_session=False)
    )
    kept = sorted({uid for (uid,) in db.query(SubCategory.categoryUid).filter(SubCategory.categoryUid.in_(saved["categories"]))})
    categories = (
        db.query(Category)
        .filter(Category.categoryUid.in_(saved["categories"]), Category.categoryUid.notin_(kept), Category.updatedBy == ADDED_BY)
        .delete(synchronize_session=False)
    )
    db.commit()
    return options, categories, kept


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", nargs="?", type=Path, help="the JSON file of categories and options to add")
    parser.add_argument("--apply", action="store_true", help="add what's missing (default: preview only)")
    parser.add_argument("--undo", type=Path, metavar="BACKUP", help="remove exactly what a backup lists")
    parser.add_argument("--tenant", default=settings.DEFAULT_TENANT_ID)
    args = parser.parse_args()
    if bool(args.file) == bool(args.undo):
        parser.error("give either the options file or --undo BACKUP")

    from scripts._tenant_db import tenant_engine  # local: needs the app's settings, never the test ones

    db = sessionmaker(bind=tenant_engine(args.tenant))()
    try:
        if args.undo:
            options, categories, kept = undo(db, args.undo, args.tenant)
            print(f"Removed {options} option(s) and {categories} category(ies) listed in {args.undo.name}."
                  + (f" Kept categories that have gained options since: {', '.join(kept)}" if kept else ""))
            return
        steps, problems = preview(db, load_plan(args.file))
        if problems:
            raise SystemExit("\nStopped - nothing written:\n  " + "\n  ".join(problems))
        new_categories = sum(1 for s in steps if s.category_uid is None)
        new_options = sum(len(s.options) for s in steps)
        summary = f"{new_categories} category(ies) and {new_options} option(s)"
        if not args.apply:
            print(f"\nPreview only: {summary} would be added. Run again with --apply to add them.")
        elif new_categories or new_options:
            print(f"\nAdded {summary}. Undo file: {apply(db, steps, args.tenant)}")
        else:
            print("\nNothing to add - everything is already there.")
    finally:
        db.close()


if __name__ == "__main__":
    main()

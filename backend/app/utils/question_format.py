"""A question (`questions` row) as the other system stores it (user, 2026-10-17) - the one module that
knows that format. The app keeps seeing each option as {"id", "text"} and one correct option id.

    options         ["Good", "Bad"] - the options' plain texts; the app is shown ids "1", "2", ...
                    (each option's position, which is also what an answer is saved as -
                    services/answer_numbers.py)
    correct_answer  ["2"] - the correct options' positions; more than one on a multi-answer question
    settings        {"timer": 30, "required": true, "shuffle": true} - timer 0 = none set
    descriptions    the explanation shown with the answer

Rows this app wrote before - options as [{"id": "A", "text": "..."}], the key as one bare value ("2",
or the option's id from before numbering), {"timerSeconds", "explanation"} settings - read the same;
scripts/align_question_records.py converts them."""

import json
from typing import Any, Iterable, Optional


def _parsed(stored: Optional[str]) -> Any:
    try:
        return json.loads(stored) if stored else None
    except (ValueError, TypeError):
        return None


def _compact(value: Any) -> str:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def options(question) -> list[dict[str, str]]:
    """The question's options as the app sees them, in order: {"id", "text"} - a plain-text option's
    id is its position ("1", "2", ...), an option written before keeps its own id."""
    parsed = _parsed(question.options)
    if not isinstance(parsed, list):
        return []
    shown = []
    for position, option in enumerate(parsed, start=1):
        if isinstance(option, dict):  # written before: {"id", "text"}
            shown.append({"id": str(option.get("id")), "text": str(option.get("text") or "")})
        elif option is not None and not isinstance(option, list):
            shown.append({"id": str(position), "text": str(option)})
    return shown


def stored_options(texts: Iterable[str]) -> Optional[str]:
    """What to store for options with these texts, in order; None for none."""
    texts = [str(text) for text in texts]
    return _compact(texts) if texts else None


def key_values(question) -> list[str]:
    """The answer key's values as stored: each correct option's position ("2") - or, written before,
    one bare value (a position, or the option's id from before numbering). [] when there is none."""
    stored = question.correct_answer
    if stored is None or not str(stored).strip():
        return []
    parsed = _parsed(stored)
    if isinstance(parsed, list):
        return [str(value).strip() for value in parsed if value is not None and str(value).strip()]
    return [str(stored).strip()]


def stored_key(positions: Iterable[int]) -> Optional[str]:
    """What to store for an answer key naming these option positions; None for none."""
    positions = [str(position) for position in positions]
    return _compact(positions) if positions else None


def _settings(question) -> dict:
    parsed = _parsed(question.settings)
    return parsed if isinstance(parsed, dict) else {}


def timer_seconds(question) -> Optional[int]:
    """The question's own answering time in seconds; None when it has none (0, or not set)."""
    settings = _settings(question)
    try:
        seconds = int(settings.get("timer", settings.get("timerSeconds")) or 0)
    except (ValueError, TypeError):
        return None
    return seconds if seconds > 0 else None


def stored_settings(timer: Optional[int]) -> str:
    """What to store for a question's settings, as the other system writes a question's."""
    return _compact({"timer": int(timer or 0), "required": True, "shuffle": True})


def explanation(question) -> Optional[str]:
    """The explanation shown with the answer: `descriptions`, or the one an older row kept in its
    settings."""
    older = _settings(question).get("explanation")
    if older:
        return str(older)
    return (getattr(question, "descriptions", None) or "").strip() or None

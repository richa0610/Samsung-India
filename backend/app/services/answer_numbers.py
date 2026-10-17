"""Answers saved as option NUMBERS (user, 2026-10-16): `assessment.selectedOption` and the answer key in
`questions.correct_answer` hold the option's position in the question's option list - 1 = the first
option shown. Since 2026-10-17 Survey answers are numbered the same way (user), and questions are
stored the other system's way (app/utils/question_format.py): plain-text options, whose ids in the app
ARE their positions, and the key as a list of positions (["2"]).

The app keeps sending and receiving each option's own id: an id it sends becomes its number before it
is saved (`number_for`), and a saved number becomes the id again for anything the app is shown
(`option_id`). Scoring compares numbers (`is_correct`).

A saved value that isn't a number - one saved before numbering, or an answer key written as a letter -
is still read as the option id it is, so both kinds keep working. A question whose option list can't
be read has nothing to number: its values are kept and compared as written, as before.
"""

from typing import Optional

from app.utils import question_format


def option_ids(question) -> list[str]:
    """The question's option ids, in the order they are shown (none when its options can't be read)."""
    return [option["id"] for option in question_format.options(question)]


def number_for(question, option_id: Optional[str]) -> Optional[str]:
    """What to save for the option the app sent: its number ("2"), or None when nothing was picked or
    it isn't one of this question's options."""
    if option_id is None:
        return None
    ids = option_ids(question)
    if not ids:
        return option_id
    return str(ids.index(option_id) + 1) if option_id in ids else None


def position(question, saved: Optional[str]) -> Optional[int]:
    """The option (1 = first) a saved answer or key value names: a number, or - saved before
    numbering - the option's own id. None when it names none of this question's options."""
    value = (saved or "").strip()
    ids = option_ids(question)
    if not value or not ids:
        return None
    if value.isdigit():
        number = int(value)
        return number if 1 <= number <= len(ids) else None
    return ids.index(value) + 1 if value in ids else None


def option_id(question, saved: Optional[str]) -> Optional[str]:
    """The option id the app shows for a saved answer or key value, or None when it names none."""
    ids = option_ids(question)
    if not ids:
        return saved or None
    number = position(question, saved)
    return ids[number - 1] if number else None


def correct_option_id(question) -> Optional[str]:
    """The correct option's id, as the app shows it (the first, on a multi-answer question); None for
    a question with no key (a survey)."""
    keys = question_format.key_values(question)
    return option_id(question, keys[0]) if keys else None


def is_correct(question, saved_answer: Optional[str]) -> bool:
    """Whether a saved answer is right: it picks the correct option - a multi-answer question's key
    names several, which one pick can't match."""
    keys = question_format.key_values(question)
    if not option_ids(question):
        return bool(saved_answer) and keys == [saved_answer]
    picked = position(question, saved_answer)
    return picked is not None and {position(question, key) for key in keys} == {picked}

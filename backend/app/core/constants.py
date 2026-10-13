# A result at or above this percentage counts as a pass, both on the
# trainer's session dashboard and in a trainee's own session history.
# There's no per-suite passing-score column yet, so this is a single
# global threshold. Previously duplicated as two separate constants in
# routers/training.py and routers/session.py.
PASS_THRESHOLD_PERCENT = 50

# How many times a trainer may lift one trainee's proctoring lockout in one training. Once they're
# all used, the trainee stays locked out of that training's test.
MAX_PROCTORING_UNLOCKS = 2

# What an unlock adds to the trainee's `theftAttemptsLeft` countdown (user, 2026-10-12: add, never
# reset - and the trainee's strike totals are kept). See services/proctoring_strikes.py.
PROCTORING_UNLOCK_ADDED_ATTEMPTS = 3

# The on-device proctoring reasons the trainee's app reports (src/components/proctoring/violations.ts).
PROCTORING_VIOLATIONS = (
    "SIDE-LOOK DETECTED",
    "MULTIPLE PEOPLE DETECTED",
    "NO FACE DETECTED",
    "EXCESSIVE HEAD TILT",
    "TAB SWITCH DETECTED",
)

# Trainees can't yet pick which trainer's session to join - that'll come
# from scanning a QR code or entering a trainer ID. Until then, the trainee
# app only ever shows this trainer's session.
DEMO_TRAINER_EMPLOYEE_ID = "demotrainer"

# The order modules run in within a session. LIVE_QUIZ has no dedicated
# Conference column (unlike the other three) so it's detected from
# `sessionConfig` instead - see services/module_flow.py's configured_modules.
MODULE_SEQUENCE = ["ATTENDANCE", "STANDARD_TEST", "LIVE_QUIZ", "SURVEY"]

MODULE_LABELS = {
    "ATTENDANCE": "Attendance Module",
    "STANDARD_TEST": "Standard Test Module",
    "LIVE_QUIZ": "Live Quiz Module",
    "SURVEY": "Survey Module",
}

# The short names, where "Module" would only crowd the screen (the trainee's session flow).
MODULE_NAMES = {
    "ATTENDANCE": "Attendance",
    "STANDARD_TEST": "Standard Test",
    "LIVE_QUIZ": "Live Quiz",
    "SURVEY": "Survey",
}

# Maps a module key to the key it's stored under in `sessionConfig` -
# ATTENDANCE isn't here because it doesn't have an `unlockCondition`; it
# only ever unlocks via the training service's start_training.
MODULE_CONFIG_KEY = {
    "STANDARD_TEST": "standardTest",
    "LIVE_QUIZ": "liveQuiz",
    "SURVEY": "survey",
}

AUTO_ADVANCE_PERFORMER = "system:auto-advance"

# Live Quiz (FFF) real-time state, stored on `conference.liveQuizState`.
# IDLE/WAITING are the lobby (module active, nothing broadcast); QUESTION_LIVE
# means `liveQuestionId` + `liveTimerEndsAt` are set; FINISHED is terminal and
# triggers the one-shot scoring pass. See services/live_quiz_service.py.
LIVE_QUIZ_STATE_IDLE = "IDLE"
LIVE_QUIZ_STATE_QUESTION_LIVE = "QUESTION_LIVE"
LIVE_QUIZ_STATE_LEADERBOARD = "LEADERBOARD"
LIVE_QUIZ_STATE_FINISHED = "FINISHED"

# Fallback per-question countdown when a question has no `timerSeconds` in its
# `settings` JSON blob.
LIVE_QUIZ_DEFAULT_TIMER_SECONDS = 30

# Fallback title for training sessions when neither a specific suiteTitle nor
# trainingType is available.
DEFAULT_SESSION_TITLE = "Training Session"

# Display name for a result or attendance row whose trainee record is missing.
UNKNOWN_TRAINEE_NAME = "Unknown Trainee"

# The master-list categories whose approved subcategories are the Add Training form's options,
# found by name (any letter case / spacing) - category IDs differ from one database to another,
# so none is written into code (user, 2026-10-13).
AUDIENCE_CATEGORY = "Audience"
SESSION_TYPE_CATEGORY = "Session Type"
TRAINING_TYPE_CATEGORY = "Training Type"
CHECKLIST_CATEGORY = "Training Checklist"
# Pickers that depend on another (user, 2026-10-13): the parent options are the approved
# categories with this `visibleOnWeb` value, and each one's own options are its approved
# subcategories - the zones (East, North, ... marked "Zone") and their regions (East 1, ...),
# the states (marked "State", entered by the admin) and their districts.
ZONE_CATEGORY_GROUP = "Zone"
STATE_CATEGORY_GROUP = "State"


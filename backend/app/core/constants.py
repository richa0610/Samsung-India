# A result at or above this percentage counts as a pass, both on the
# trainer's session dashboard and in a trainee's own session history.
# There's no per-suite passing-score column yet, so this is a single
# global threshold. Previously duplicated as two separate constants in
# routers/training.py and routers/session.py.
PASS_THRESHOLD_PERCENT = 50

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

"""The admin / trainer side of one training, split by job (this was services/training_service.py):

- management          create, read for editing, update, approve / reject
- listing             trainer Home summary, Training / Pending lists and filters, attendance list
- session_start       the start-session gates (geofence, schedule) and starting a session
- session_control     starting / restarting / stopping / advancing modules, ending a session
- attendance_actions  manual Present / Absent, proctoring unlock, attendance reset
- session_dashboard   the Session Dashboard, join code, all performers, session report
- timeline            execution flow, audit log, Session Heroes, module run time
- common              what several of these share: the access check, the live-room nudge, TrainingOut
"""

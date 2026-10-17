-- Test/dev seed data for mmtbtwob_tops (the real schema - see
-- mmtbtwob_tops.sql, gitignored, not committed).
-- NOT part of the org's authoritative dump — safe to re-run against a fresh
-- import, and safe to delete once the app is wired to real trainer/admin flows.
--
-- Scenario seeded: one approved, already-started training session
-- ("conference") for the currently registered trainee (Aman Kumar Gautam),
-- with Attendance + Standard Test + Survey enabled in its session
-- flow (Live Quiz intentionally left out of this session — see step 2).
--
-- Run in phpMyAdmin (SQL tab) against mmtbtwob_tops, or:
--   mysql -u root mmtbtwob_tops < backend/seed_test_data.sql
--
-- Note: this script assumes a trainee named "Aman Kumar Gautam" (phone
-- 8287045234, traineeUid 42a982b39caf4715b6a29ea394572afb) already exists -
-- insert one first if starting from a fresh database. It also assumes the
-- app's session-selection logic (see routers/session.py) picks conferences
-- by trainerEmployeeId == "demotrainer" and conferenceStatus == "Ongoing" -
-- adjust those columns after seeding if they don't already match.

-- ---------------------------------------------------------------
-- Step 1: system_modules — lookup table for the four session-flow modules
-- ---------------------------------------------------------------
INSERT INTO `system_modules` (`module_key`, `module_name`) VALUES
('ATTENDANCE', 'Attendance'),
('STANDARD_TEST', 'Standard Test'),
('LIVE_QUIZ', 'Live Quiz (FFF)'),
('SURVEY', 'Survey');

-- ---------------------------------------------------------------
-- Step 2: conference — the training session itself (what session_detail.tsx
-- should eventually render). Admin-approved and already started by the
-- trainer (activeModuleId = ATTENDANCE), so the trainee can check in now.
-- ---------------------------------------------------------------
INSERT INTO `conference` (
  `conferenceUid`, `zone`, `region`, `company`, `requestedBy`,
  `trainerEmployeeId`, `trainerName`,
  `conferenceType`, `conferenceDate`, `conferenceEndsOn`, `conferenceTime`,
  `conferenceStatus`, `activeModuleId`, `enableCheckIn`,
  `trainingHub`, `audience`, `sessionType`, `trainingType`, `batchSize`, `confirmedPax`,
  `state`, `district`, `venueUid`,
  `geoLatitude`, `geoLongitude`, `geoRadius`,
  `assessmentFor`, `suiteTitle`, `postAssessmentUid`, `surveyUid`, `noOfQuestion`,
  `sessionConfig`,
  `status`, `auditStatus`
) VALUES (
  '7cc3f30e56454ab7b393b17aa79e7906', 'North Zone', 'Delhi NCR', 'Samsung India', 'Aman Kumar Gautam',
  'EMP1042', 'Rohit Sharma',
  'Non Residential Conference', '2026-07-25', '2026-07-25', '10:00 AM',
  'Live', 'ATTENDANCE', 1,
  'Connaught Place Hub', 'PC Training', 'Classroom Training', 'Product Training', '25', '18',
  'Delhi', 'New Delhi', 'VEN-CP-001',
  28.63280000, 77.21950000, 100,
  'Post Training', 'Galaxy S26 Product Knowledge', 'b73524c374fc44159b8ad5d972f61a18', 'df1029b81b3c4d60836b50e8464f1515', '3',
  '{"attendance":{"checkInOpens":"06:00 PM","checkOutCloses":"06:20 PM","geoFencing":true},"standardTest":{"category":"Product Knowledge","startTime":"10:00 AM","endTime":"12:00 PM","checkIn":true,"unlockCondition":"Automatic"},"survey":{"category":"Feedback","startTime":"12:00 PM","endTime":"12:30 PM","checkIn":true,"unlockCondition":"Automatic"}}',
  'Approved', 'Approved'
);

-- ---------------------------------------------------------------
-- Step 3: assessmentsuite — one suite for the Standard Test, one for the Survey
-- ---------------------------------------------------------------
INSERT INTO `assessmentsuite` (`assessmentSuiteUid`, `courseName`, `examTitle`, `assessment_type`, `noOfQuestion`, `testTime`, `status`) VALUES
('b73524c374fc44159b8ad5d972f61a18', 'Galaxy S26 Product Knowledge', 'Post Training Standard Test', 'Quiz', 3, '15', 'Approved'),
('df1029b81b3c4d60836b50e8464f1515', 'Galaxy S26 Product Knowledge', 'Session Feedback Survey', 'Survey', 3, '5', 'Approved');

-- ---------------------------------------------------------------
-- Step 4: questions — 3 quiz questions (mirrors src/data/quiz.ts so the
-- eventual API swap-in is a straight passthrough) + 3 survey questions
-- ---------------------------------------------------------------
INSERT INTO `questions` (`assessmentSuiteUid`, `question`, `question_type`, `sort_order`, `options`, `correct_answer`, `points`, `descriptions`, `status`) VALUES
('b73524c374fc44159b8ad5d972f61a18',
 'Identify the INCORRECT statement about performance with Galaxy S26.',
 'multiple_choice', 1,
 '[{"id":"A","text":"Powerful 2nm Exynos 2600 Processor"},{"id":"B","text":"Larger 6.3-inch Dynamic Display"},{"id":"C","text":"Bigger 4300mAh Battery"},{"id":"D","text":"None of these"}]',
 'A', 10,
 'The Galaxy S26 is not equipped with the Exynos 2600 processor.', 'Approved'),

('b73524c374fc44159b8ad5d972f61a18',
 'Which feature is NOT part of the S26 Ultra in-store demo?',
 'multiple_choice', 2,
 '[{"id":"A","text":"Privacy display via live demo"},{"id":"B","text":"Horizontal lock via live demo"},{"id":"C","text":"Enhanced Photo Assist via live demo"},{"id":"D","text":"AI Call screening via live demo"}]',
 'D', 10,
 'AI Call screening is not included in the S26 Ultra demo flow.', 'Approved'),

('b73524c374fc44159b8ad5d972f61a18',
 'Which Galaxy AI feature helps edit a photo after it is taken?',
 'multiple_choice', 3,
 '[{"id":"A","text":"Photo Assist"},{"id":"B","text":"Live Translate"},{"id":"C","text":"Now Brief"},{"id":"D","text":"Samsung Wallet"}]',
 'A', 10,
 'Photo Assist provides AI-powered editing tools for photos.', 'Approved'),

('df1029b81b3c4d60836b50e8464f1515',
 'How would you rate the trainer''s product knowledge?',
 'multiple_choice', 1,
 '[{"id":"A","text":"Excellent"},{"id":"B","text":"Good"},{"id":"C","text":"Average"},{"id":"D","text":"Poor"}]',
 NULL, 0,
 NULL, 'Approved'),

('df1029b81b3c4d60836b50e8464f1515',
 'Was the session duration adequate?',
 'multiple_choice', 2,
 '[{"id":"A","text":"Too long"},{"id":"B","text":"Just right"},{"id":"C","text":"Too short"}]',
 NULL, 0,
 NULL, 'Approved'),

('df1029b81b3c4d60836b50e8464f1515',
 'Would you recommend this training to a colleague?',
 'multiple_choice', 3,
 '[{"id":"A","text":"Definitely"},{"id":"B","text":"Maybe"},{"id":"C","text":"No"}]',
 NULL, 0,
 NULL, 'Approved');

-- ---------------------------------------------------------------
-- Step 5: conference_activity_log — trainer already tapped "Start" on
-- Attendance, which is why conference.activeModuleId = ATTENDANCE above
-- ---------------------------------------------------------------
INSERT INTO `conference_activity_log` (`conferenceUid`, `moduleId`, `action`, `performedBy`, `trainerLat`, `trainerLng`, `locationRemark`) VALUES
('7cc3f30e56454ab7b393b17aa79e7906', 'ATTENDANCE', 'STARTED', 'Rohit Sharma', 28.63280000, 77.21950000, 'Session started at venue');

-- ---------------------------------------------------------------
-- Step 6: attendance — trainee Aman Kumar Gautam (id 3, traineeUid
-- 42a982b39caf4715b6a29ea394572afb) has already checked in to the session
-- seeded in Step 2, within the geofence.
-- ---------------------------------------------------------------
INSERT INTO `attendance` (
  `attendanceUid`, `conferenceUid`, `trainerUid`, `traineeUid`, `phone`,
  `markedOn`, `status`, `checkInPhoto`, `checkInDistance`,
  `geofenceBypass`, `attemptCount`, `isTheftLocked`, `theftAttemptsLeft`
) VALUES (
  'c27d1052906947baa3ac1a366d4c5b17', '7cc3f30e56454ab7b393b17aa79e7906', 'EMP1042', '42a982b39caf4715b6a29ea394572afb', 8287045234,
  '2026-07-25 09:15:00', 'Present', 'checkin_photos/sample_checkin.jpg', '18 meters',
  0, 1, 0, 3
);

-- ---------------------------------------------------------------
-- Step 7: trainer has moved on from Attendance to the Standard Test
-- (Tushar already checked in, so this makes the next module live for testing
-- post_test.tsx end to end without needing a trainer app yet).
-- ---------------------------------------------------------------
UPDATE `conference` SET `activeModuleId` = 'STANDARD_TEST' WHERE `conferenceUid` = '7cc3f30e56454ab7b393b17aa79e7906';

-- ---------------------------------------------------------------
-- Step 8: GET /sessions/current now picks the "current" conference purely
-- from its own `conferenceDate` + `conferenceTime` columns (see
-- app/routers/session.py::_select_current_conference) - whichever Approved
-- conference most recently started wins; if none have started yet, the
-- soonest upcoming one is returned with started=false instead.
--
-- To point the app at THIS seeded session for testing, its start time must
-- be in the past relative to your machine's clock - edit these two columns
-- (conferenceDate 'YYYY-MM-DD', conferenceTime 'HH:MM AM/PM') any time you
-- want to move it. This UPDATE sets it to "already started" as of the seed
-- date; adjust as needed.
-- ---------------------------------------------------------------
UPDATE `conference` SET `conferenceDate` = '2026-07-20', `conferenceTime` = '09:00 AM' WHERE `conferenceUid` = '7cc3f30e56454ab7b393b17aa79e7906';

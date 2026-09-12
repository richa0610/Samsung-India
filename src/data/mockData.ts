/**
 * mockData.ts — Centralized demo data for Samsung India Training App.
 *
 * Single source of truth for all frontend-only demo data.
 * No imports from api/* to avoid circular dependencies with mockService.ts.
 */

// ─── Helpers ─────────────────────────────────────────────────────────────────
const _pad2 = (n: number) => String(n).padStart(2, "0");
function _daysFromToday(offset: number): string {
  const d = new Date();
  d.setDate(d.getDate() + offset);
  return `${d.getFullYear()}-${_pad2(d.getMonth() + 1)}-${_pad2(d.getDate())}`;
}

export const TODAY_STR = _daysFromToday(0);
export const TOMORROW_STR = _daysFromToday(1);
export const YESTERDAY_STR = _daysFromToday(-1);

// ─── Trainee ─────────────────────────────────────────────────────────────────
export const DEMO_TRAINEE = {
  id: 1,
  traineeUid: "demo-trainee-uid-001",
  name: "Tushar Prajapati",
  phone: 9876543210 as number,
  email: "anshu.pandey@samsung.com",
  gender: "male" as string | null,
  designation: "Sales Associate" as string | null,
  employee_id: "EMP-20240001" as string | null,
  supervisorName: "Tushar" as string | null,
  state: "delhi" as string | null,
  district: "SOUTH" as string | null,
  profilePhoto: null as string | null,
  status: "Active",
};

// ─── Trainer Profile ───────────────────────────────────────────────────────────
export const DEMO_TRAINER_PROFILE = {
  name: "Demo Trainer",
  email: "demotrainer@123.com",
  mobileNumber: "9877521454",
  altPhone: "9898521458",
  gender: "Male",
  dob: "06/05/2002",

  city: "New Delhi",
  district: "New Delhi",
  state: "Delhi",
  pincode: "110030",
  landmark: "SBI Bank Sultanpur Branch",
  permanentSameAsLocal: false,

  aadharNumber: "",
  aadharFile: "",
  profilePicture: "",
  about: "Please design your content",
  resume: "",
  otherDocument: "",

  facebookUsername: "",
  twitterUsername: "",
  instagramUsername: "",
  linkedinUsername: "",
  youtubeUsername: "",
  github: "",

  jobStatus: "Approved",
  joinedOn: "02/01/2025",
  role: "Trainer",
  designation: "ASM",
  salary: "",
  companyEmail: "",
  visitingCard: "",
  idCard: "",
  offerLetter: "",
  letterhead: "",
  promocode: "",

  username: "demotrainer",
  password: "",
  remarks: "",
  agreedToTerms: true,
};

// ─── New Trainee Registration (Trainer-created) ───────────────────────────────
export type NewTraineeRecord = {
  traineeUid: string;
  registeredAt: string;
  approvalStatus: "Approved" | "Pending" | "Rejected";
  profilePhoto: string | null;
  agencyId: string | null;
  fullName: string;
  designation: string;
  gender: string;
  dob: string | null;
  primaryEmail: string;
  primaryPhone: string;
  altEmail: string | null;
  altPhone: string | null;
  address: string | null;
  state: string | null;
  district: string | null;
  zone: string;
  region: string;
  company: string;
  requestedBy: string;
  trainerId: string;
  trainerName: string;
  supervisorId: string;
  supervisorName: string;
  supervisorDesignation: string | null;
  joinedOn: string;
  jobStatus: string;
  jobCity: string | null;
  jobPincode: string | null;
  resignedOn: string | null;
  username: string;
  password: string;
  updatedBy: string | null;
  updationOn: string | null;
  timestamp: string | null;
};

export const DEMO_AUTH_SESSION = {
  access_token: "demo-access-token-trainee",
  token_type: "bearer",
  trainee: { ...DEMO_TRAINEE },
};

// ─── Admin / Trainer ──────────────────────────────────────────────────────────
export const DEMO_ADMIN_TRAINER = {
  username: "trainer1",
  name: "Rajesh Kumar",
  role: "trainer",
  offerId: "OFF-DEMO-001",
};
export const DEMO_ADMIN_ADMIN = {
  username: "admin",
  name: "Tushar",
  role: "admin",
};

export const DEMO_ADMIN_SESSION_TRAINER = {
  access_token: "demo-access-token-trainer",
  token_type: "bearer",
  admin: { ...DEMO_ADMIN_TRAINER },
};

export const DEMO_ADMIN_SESSION_ADMIN = {
  access_token: "demo-access-token-admin",
  token_type: "bearer",
  admin: { ...DEMO_ADMIN_ADMIN },
};

// ─── Current Session (Trainee view) ──────────────────────────────────────────
export const DEMO_CURRENT_SESSION = {
  conferenceUid: "demo-conf-uid-main",
  title: "Training Session",
  sessionType: "One-Day Session" as string | null,
  date: "06 Jun 2026" as string | null,
  location: "New Delhi" as string | null,
  trainerName: "Rajesh Kumar" as string | null,
  confirmationStatus: "Not Confirmed",
  started: true,
  startsAt: "09:00 AM" as string | null,
  attendanceGeoFencing: true,
  modules: [
    {
      key: "ATTENDANCE" as
        | "ATTENDANCE"
        | "STANDARD_TEST"
        | "LIVE_QUIZ"
        | "SURVEY",
      name: "ATTENDANCE",
      time: "09:00" as string | null,
      endTime: "10:00" as string | null,
      duration: "1h" as string | null,
      isLive: true,
      isCompleted: false,
      isMissed: false,
      completedAt: null as string | null,
      score: null as string | null,
      ranDuration: null as string | null,
      assessmentSuiteUid: null as string | null,
    },
    {
      key: "LIVE_QUIZ" as
        | "ATTENDANCE"
        | "STANDARD_TEST"
        | "LIVE_QUIZ"
        | "SURVEY",
      name: "QUIZ",
      time: "10:00" as string | null,
      endTime: "12:00" as string | null,
      duration: "2h" as string | null,
      isLive: false,
      isCompleted: false,
      isMissed: false,
      completedAt: null as string | null,
      score: null as string | null,
      ranDuration: "Ran : 1h 55m" as string | null,
      assessmentSuiteUid: "suite-quiz-001" as string | null,
    },
    {
      key: "STANDARD_TEST" as
        | "ATTENDANCE"
        | "STANDARD_TEST"
        | "LIVE_QUIZ"
        | "SURVEY",
      name: "POST TEST",
      time: "12:00" as string | null,
      endTime: "14:00" as string | null,
      duration: "2h" as string | null,
      isLive: false,
      isCompleted: false,
      isMissed: false,
      completedAt: null as string | null,
      score: null as string | null,
      ranDuration: null as string | null,
      assessmentSuiteUid: "suite-post-test-001" as string | null,
    },
    {
      key: "SURVEY" as "ATTENDANCE" | "STANDARD_TEST" | "LIVE_QUIZ" | "SURVEY",
      name: "SURVEY",
      time: "14:00" as string | null,
      endTime: "16:00" as string | null,
      duration: "2h" as string | null,
      isLive: false,
      isCompleted: false,
      isMissed: false,
      completedAt: null as string | null,
      score: null as string | null,
      ranDuration: null as string | null,
      assessmentSuiteUid: "suite-survey-001" as string | null,
    },
  ],
};

// ─── Session History (Trainee) ────────────────────────────────────────────────
export const DEMO_SESSION_HISTORY = [
  {
    conferenceUid: "hist-conf-001",
    title: "Samsung Galaxy S25 Flagship Training",
    date: "2026-07-10" as string | null,
    trainerName: "Sunita Patel" as string | null,
    attendanceStatus: "Present" as string | null,
    score: "88%" as string | null,
    passed: true as boolean | null,
  },
  {
    conferenceUid: "hist-conf-002",
    title: "Samsung Smart Home Ecosystem Workshop",
    date: "2026-06-22" as string | null,
    trainerName: "Vikram Nair" as string | null,
    attendanceStatus: "Present" as string | null,
    score: "72%" as string | null,
    passed: true as boolean | null,
  },
  {
    conferenceUid: "hist-conf-003",
    title: "Galaxy AI Features Deep Dive",
    date: "2026-05-18" as string | null,
    trainerName: "Ananya Reddy" as string | null,
    attendanceStatus: "Present" as string | null,
    score: "56%" as string | null,
    passed: false as boolean | null,
  },
];

// ─── MCQ Questions (Post Test / Live Quiz) ────────────────────────────────────
export const DEMO_ASSESSMENT_QUESTIONS = [
  {
    id: 1,
    question:
      "Identify the INCORRECT statement about performance with Galaxy S26.",
    question_type: "multiple_choice",
    sort_order: 1,
    correctAnswer: "A",
    explanation:
      "The Galaxy S26 is not equipped with the Exynos 2600. It uses the Snapdragon 8 Gen 4 Chipset.",
    options: [
      { id: "A", text: "Powerful 2nm Exynos 2600 Processor" },
      { id: "B", text: "Larger 6.3-inch Dynamic Display" },
      { id: "C", text: "Bigger 4300mAh Battery" },
      { id: "D", text: "None of these" },
    ],
  },
  {
    id: 2,
    question: "Which of the following is NOT part of S26 Ultra In-store demo?",
    question_type: "multiple_choice",
    sort_order: 2,
    correctAnswer: "D",
    explanation:
      "The Galaxy S26 is not equipped with the Exynos 2600. It uses the Snapdragon 8 Gen 4 Chipset.",
    options: [
      { id: "A", text: "Privacy display via live demo" },
      { id: "B", text: "Horizontal lock via live demo" },
      { id: "C", text: "Enhanced Photo Assist via live demo" },
      { id: "D", text: "AI Call screening via live demo" },
    ],
  },
  {
    id: 3,
    question: "Which Galaxy AI feature helps edit a photo after it is taken?",
    question_type: "multiple_choice",
    sort_order: 3,
    correctAnswer: "A",
    explanation:
      "Photo Assist offers AI generative editing tools to move, resize, or delete objects in photos.",
    options: [
      { id: "A", text: "Photo Assist" },
      { id: "B", text: "Live Translate" },
      { id: "C", text: "Now Brief" },
      { id: "D", text: "Samsung Wallet" },
    ],
  },
  {
    id: 4,
    question: "What is the battery capacity of the Samsung Galaxy S26 Ultra?",
    question_type: "multiple_choice",
    sort_order: 4,
    correctAnswer: "C",
    explanation:
      "The Galaxy S26 Ultra features a robust 5000mAh all-day intelligent battery.",
    options: [
      { id: "A", text: "4500mAh" },
      { id: "B", text: "4800mAh" },
      { id: "C", text: "5000mAh" },
      { id: "D", text: "5500mAh" },
    ],
  },
  {
    id: 5,
    question:
      "Which Galaxy AI feature powers on-device productivity summaries?",
    question_type: "multiple_choice",
    sort_order: 5,
    correctAnswer: "A",
    explanation:
      "Now Brief aggregates summaries and upcoming schedules directly on your screen.",
    options: [
      { id: "A", text: "Now Brief" },
      { id: "B", text: "Bixby Routine" },
      { id: "C", text: "Samsung Pass" },
      { id: "D", text: "Good Lock" },
    ],
  },
  {
    id: 6,
    question: "What display technology does the Galaxy S26 series use?",
    question_type: "multiple_choice",
    sort_order: 6,
    correctAnswer: "B",
    explanation:
      "The Galaxy S26 series utilizes Dynamic AMOLED 2X displays with up to 120Hz adaptive refresh rate.",
    options: [
      { id: "A", text: "LCD" },
      { id: "B", text: "Dynamic AMOLED 2X" },
      { id: "C", text: "Super AMOLED" },
      { id: "D", text: "OLED Pro" },
    ],
  },
  {
    id: 7,
    question: "Samsung Galaxy S26 supports which maximum wired charging speed?",
    question_type: "multiple_choice",
    sort_order: 7,
    correctAnswer: "C",
    explanation: "Galaxy S26 supports up to 45W Super Fast Charging 2.0.",
    options: [
      { id: "A", text: "25W" },
      { id: "B", text: "35W" },
      { id: "C", text: "45W" },
      { id: "D", text: "65W" },
    ],
  },
  {
    id: 8,
    question:
      "Which Samsung feature enables real-time language translation during calls?",
    question_type: "multiple_choice",
    sort_order: 8,
    correctAnswer: "B",
    explanation:
      "Live Translate delivers two-way voice and text translations in real time during phone calls.",
    options: [
      { id: "A", text: "Chat Assist" },
      { id: "B", text: "Live Translate" },
      { id: "C", text: "Interpreter" },
      { id: "D", text: "Bixby Translate" },
    ],
  },
  {
    id: 9,
    question: "What is the S Pen pressure sensitivity in the Galaxy S26 Ultra?",
    question_type: "multiple_choice",
    sort_order: 9,
    correctAnswer: "C",
    explanation:
      "The integrated S Pen provides 4096 levels of precise pressure sensitivity.",
    options: [
      { id: "A", text: "1024 levels" },
      { id: "B", text: "2048 levels" },
      { id: "C", text: "4096 levels" },
      { id: "D", text: "8192 levels" },
    ],
  },
  {
    id: 10,
    question: "Which OS ships with the Samsung Galaxy S26 series at launch?",
    question_type: "multiple_choice",
    sort_order: 10,
    correctAnswer: "B",
    explanation:
      "The Samsung Galaxy S26 series debuts with One UI 7.0 based on Android 15.",
    options: [
      { id: "A", text: "One UI 6.0 / Android 14" },
      { id: "B", text: "One UI 7.0 / Android 15" },
      { id: "C", text: "One UI 8.0 / Android 16" },
      { id: "D", text: "One UI 6.5 / Android 15" },
    ],
  },
];

// ─── Survey Questions ─────────────────────────────────────────────────────────
export const DEMO_SURVEY_QUESTIONS = [
  {
    id: 101,
    question: "How would you rate the June Activity-led classroom session?",
    question_type: "multiple_choice",
    sort_order: 1,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 102,
    question:
      "How effective is K.C.D. approach for Sales pitch practice & recall?",
    question_type: "multiple_choice",
    sort_order: 2,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 103,
    question:
      "How effective was the activity to use Galaxy AI features to create Team Name, Anthem & Logo?",
    question_type: "multiple_choice",
    sort_order: 3,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 104,
    question:
      "How effective was the 'Samsung Dangal' activity to practice countering competition?",
    question_type: "multiple_choice",
    sort_order: 4,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 105,
    question:
      "How effective is Activity-led training sessions vs. regular training session?",
    question_type: "multiple_choice",
    sort_order: 5,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 106,
    question:
      "How clear and engaging was the trainer's explanation of new features?",
    question_type: "multiple_choice",
    sort_order: 6,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 107,
    question:
      "How confident do you feel applying these learnings on the sales floor?",
    question_type: "multiple_choice",
    sort_order: 7,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 108,
    question:
      "How satisfied are you with the interactive demo units and learning materials provided?",
    question_type: "multiple_choice",
    sort_order: 8,
    options: [
      { id: "A", text: "Very Effective" },
      { id: "B", text: "Effective" },
      { id: "C", text: "Neutral" },
      { id: "D", text: "Ineffective" },
      { id: "E", text: "Very Ineffective" },
    ],
  },
  {
    id: 109,
    question: "What do you like most about the trainer?",
    question_type: "short_answer",
    sort_order: 9,
    options: [] as { id: string; text: string }[],
  },
  {
    id: 110,
    question: "Additional Comments",
    question_type: "short_answer",
    sort_order: 10,
    options: [] as { id: string; text: string }[],
  },
];

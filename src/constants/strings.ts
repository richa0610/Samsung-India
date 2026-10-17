/**
 * App-wide display text. Change the brand or a screen's wording here - the screens read it from
 * these constants instead of hard-coding it.
 */

export const BRAND = {
  /** The wordmark. */
  name: "TOPS",
  /** The spaced-out line under the wordmark. */
  region: "",
  /** The footer's three-word line. */
  tagline: ["People", "Learning", "Innovation"],
} as const;


export type LoginSlide = { headline: string; body: string };

export const LOGIN_TEXT = {
  /** The hero carousel - one slide per entry. */
  slides: [
    { headline: "Learn.\nAssess.\nGrow together.", body: "Access your trainings, assessments and track your progress." },
    { headline: "Join in\nseconds.", body: "Scan your session QR or sign in with your Company ID." },
    { headline: "See how\nyou're doing.", body: "Your scores, rank and training history in one place." },
  ] satisfies LoginSlide[],
  title: "Participant Login",
  subtitle: "Join your training or assessment \nto continue.",
  viaQr: "Via QR",
  viaUsername: "Via Username",
  divider: "or",
  staffPrompt: "Are you a trainer or admin?",
  staffLink: "Login here",
} as const;

/** The trainer / admin sign-in screen (one screen, worded for the role picked in "Login as"). */
export const STAFF_LOGIN_TEXT = {
  trainer: {
    tag: "Trainer Login",
    headline: "Create. Conduct",
    headlineAccent: "Track Progress.",
    body: "Manage trainings, assessments and participants with ease.",
    cardTitle: "Trainer Login",
    cardSubtitle: "Enter your details to login",
    idLabel: "Company ID / Phone No",
    idPlaceholder: "Enter Company ID or Phone No",
    submit: "Login as Trainer",
  },
  admin: {
    tag: "Admin Login",
    headline: "Manage. Monitor.",
    headlineAccent: "Drive Results.",
    body: "Manage users, trainings, assessments and platform settings.",
    cardTitle: "Admin Login",
    cardSubtitle: "Enter your admin username and password.",
    idLabel: "Username",
    idPlaceholder: "Enter username",
    submit: "Login as Admin",
  },
  passwordLabel: "Password",
  passwordPlaceholder: "Enter Password",
  forgot: "Forgot password?",
  forgotTitle: "Forgot password?",
  forgotMessage: "Please contact your administrator to reset your password.",
  secureTitle: "Your information is secure",
  secureBody: "We keep your data safe and confidential.",
  back: "Back",
} as const;

/** The "Login as" sheet that "Login here" opens. */
export const LOGIN_ROLE_TEXT = {
  title: "Login as",
  subtitle: "Choose your role to continue",
  close: "Close",
  trainer: {
    title: "Trainer",
    body: "Create and manage trainings, assess participants ",
  },
  admin: {
    title: "Admin",
    body: "Manage users, trainings, assessments",
  },
  cancel: "Cancel",
} as const;

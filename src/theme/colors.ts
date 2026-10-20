/** Single unified design tokens across the application */
export const BRAND_BLUE = "#0A61FF";
export const SUCCESS_GREEN = "#16A34A";
export const SUCCESS_BG = "#ECFDF5";
export const DANGER_RED = "#DC2626";
export const DANGER_BG = "#FEE2E2";
export const WARNING_YELLOW = "#F59E0B";
export const ACCENT_PURPLE = "#6734FF";
export const TEXT_BLACK = "#111827";
export const TEXT_MUTED = "#4B5563";
export const BORDER_COLOR = "#EAECF0";
export const BG_TINT_BLUE = "#EEF4FF";
export const GRAY_MUTED = "#D1D5DB";
export const SURFACE_MUTED = "#F3F4F6";
export const SURFACE_BLUE_SOFT = "#DDEEFF";
// Colours from the login landing's design that the palette above doesn't have.
export const HERO_BLUE_DEEP = "#0041C6";
export const HERO_SKY = "#36A8FE";
export const ACCENT_BLUE = "#054AF9";
export const TEXT_SECONDARY = "#6F7586";

export const Colors = {
  // Brand & Primary
  blue: BRAND_BLUE,
  primary: BRAND_BLUE,
  primaryDark: BRAND_BLUE,
  brandBlue: BRAND_BLUE,
  blueAccent: BRAND_BLUE,
  blue400: BRAND_BLUE,
  toggleBlue: BRAND_BLUE,
  mainColour1: BRAND_BLUE,
  copyIconColour: BRAND_BLUE,
  headerBlue: BRAND_BLUE,
  brandWordmark: ACCENT_BLUE,
  loginAccent: ACCENT_BLUE,

  // Backgrounds & Surfaces
  background: BG_TINT_BLUE,
  blue50: BG_TINT_BLUE,
  brandTintSoft: BG_TINT_BLUE,
  authPageTop: BG_TINT_BLUE,
  authSecureBg: BG_TINT_BLUE,
  roleTrainerBg: BG_TINT_BLUE,
  white: "#FFFFFF",
  gray50: "#F9FAFB",
  gray100: SURFACE_MUTED,
  slate100: SURFACE_MUTED,
  waitingBlueBg: SURFACE_BLUE_SOFT,
  notificationBg: SURFACE_BLUE_SOFT,
  notificationIconBg: "#CBE5FF",

  // Text & Headings
  black: TEXT_BLACK,
  textHeading: TEXT_BLACK,
  sheetTitle: TEXT_BLACK,
  roleCardTitle: TEXT_BLACK,
  authHeadline: TEXT_BLACK,
  authLabel: TEXT_BLACK,
  authSecureTitle: TEXT_BLACK,

  // Muted & Supporting Text
  gray800: TEXT_BLACK,
  gray700: "#374151",
  gray600: TEXT_MUTED,
  gray500: TEXT_MUTED,
  textSupporting: TEXT_MUTED,
  bottomNavInactive: TEXT_MUTED,
  sheetSubtitle: TEXT_MUTED,
  sheetClose: TEXT_MUTED,
  neutralButtonText: "#4F5061",
  roleTrainerText: TEXT_MUTED,
  roleAdminText: TEXT_MUTED,
  authBodyText: TEXT_MUTED,
  authCardSubtitle: TEXT_MUTED,
  authSecureText: TEXT_MUTED,
  authPlaceholder: "#9CA3AF",
  gray400: "#9CA3AF",
  loginSubtext: TEXT_SECONDARY,

  // Borders & Dividers
  borderLight: BORDER_COLOR,
  gray200: BORDER_COLOR,
  slate200: BORDER_COLOR,
  surfaceBorder: BORDER_COLOR,
  authCardBorder: BORDER_COLOR,
  authInputBorder: BORDER_COLOR,
  roleTrainerBorder: BORDER_COLOR,
  neutralButtonBg: BORDER_COLOR,
  borderColour: BORDER_COLOR,

  // Rails, Handles & Subtle Indicators
  gray300: GRAY_MUTED,
  timelineRail: GRAY_MUTED,
  sheetHandle: GRAY_MUTED,

  // Feedback: Success
  success: SUCCESS_GREEN,
  statusGreen: SUCCESS_GREEN,
  recordedGreen: SUCCESS_GREEN,
  successTeal: SUCCESS_GREEN,
  excelIconColour: SUCCESS_GREEN,
  successBackground: SUCCESS_BG,
  successBgSoft: SUCCESS_BG,
  recordedGreenBg: SUCCESS_BG,

  // Feedback: Danger / Error
  danger: DANGER_RED,
  red: DANGER_RED,
  pdfIconColour: DANGER_RED,
  dangerBg: DANGER_BG,
  dangerBgSoft: DANGER_BG,

  // Feedback: Warning & Attention
  warning: WARNING_YELLOW,
  statusYellow: WARNING_YELLOW,
  pendingColour: WARNING_YELLOW,

  // Accents & Roles
  csvIconColour: ACCENT_PURPLE,
  roleAdminIcon: ACCENT_PURPLE,
  roleTrainerIcon: BRAND_BLUE,
  roleTrainerChevron: BRAND_BLUE,
  roleAdminChevron: BRAND_BLUE,
  roleAdminBg: "#F5F1FF",
  roleAdminBorder: "#ECE8F8",
  roleAdminTile: "#E6DFFC",
  roleTrainerTile: "#E2EDFD",

  // Audience tags (Session Dashboard participant list: ASN / UASN / FRESH)
  audienceAssignedText: "#D97706",
  audienceAssignedBg: "#FFFBEB",
  audienceAssignedBorder: "#FDE68A",
  audienceUnassignedText: ACCENT_PURPLE,
  audienceUnassignedBg: "#F5F1FF",
  audienceUnassignedBorder: "#C4B5FD",
  audienceFreshText: BRAND_BLUE,
  audienceFreshBg: BG_TINT_BLUE,
  audienceFreshBorder: BRAND_BLUE,

  // Form Inputs
  inputColour: "#4D4D4D",
  inputColour2: "#4D4D4D33",
  inputColour3: "rgba(77, 77, 77, 0.6)",
  authInputIcon: "#3F4250",

  // Auth Specific
  authBrandDeep: BRAND_BLUE,
  authTagUnderline: BRAND_BLUE,
  authHeadlineAccent: BRAND_BLUE,
  authLink: BRAND_BLUE,
  authBackArrow: BRAND_BLUE,
  authIconTile: "#EAF4FE",
  authIcon: BRAND_BLUE,
  authButtonStart: BRAND_BLUE,
  authButtonEnd: BRAND_BLUE,
  authSecureTile: "#DCEDFF",
  authSecureIcon: BRAND_BLUE,

  // Hero & Visual Effects
  heroBlueDeep: HERO_BLUE_DEEP,
  heroSkyGlow: HERO_SKY,
  heroWaveSky: "#8FBCFF",
  heroWaveMist: "#C9DFFE",
  onHero: "#FFFFFF",
  onHeroMuted: "#C3DFFF",
  onHeroFaint: "rgba(255, 255, 255, 0.45)",
  homeGlow: "rgba(6, 52, 163, 0.35)",

  // Illustrations
  illustrationNavy: HERO_BLUE_DEEP,
  illustrationShadow: "rgba(0, 65, 198, 0.4)",
  illustrationPhoneLight: BRAND_BLUE,
  illustrationPhoneDeep: ACCENT_BLUE,
  illustrationScreenTint: "#E1EAFF",
  illustrationSky: BRAND_BLUE,
  illustrationSkyLight: HERO_SKY,
  illustrationLine: "#93B4FF",
  illustrationLineSoft: "#C7D7FF",
  illustrationPurple: ACCENT_PURPLE,
  illustrationPurpleLight: "#A78BFA",
  illustrationPurpleTint: "#DDD6FE",
  illustrationGlow: "#E6F1FF",
};
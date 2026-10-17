import { FontSize } from "./typography";

export const IconDimensions = {
  small: 14,
  caption: 16,
  default: 60,
  profile: 131,
  timer: 103,
} as const;

/** @deprecated Use `FontSize` or `Typography` from `@/theme/typography` */
export const Fonts = {
  h1: FontSize.h1,
  h2: FontSize.h2,
  h3: FontSize.h3,

  bodyLg: FontSize.body,
  body: FontSize.label,
  bodySm: FontSize.caption,

  caption: FontSize.overline,
  overline: FontSize.tiny,

  xs: FontSize.caption,
  xl: FontSize.h3,
  lg: FontSize.h2,
  br: FontSize.display,

  smallIcon: IconDimensions.small,
  captionIcon: IconDimensions.caption,
  iconSize: IconDimensions.default,
  profileIconSize: IconDimensions.profile,
  timerIconSize: IconDimensions.timer,
} as const;

export const FontSize = {
  display: 32,
  h1: 28,
  h2: 24,
  h3: 20,
  heading: 14,
  body: 16,
  bodySmall: 15,
  label: 14,
    caption: 12,
  overline: 11,
  tiny: 10,
} as const;

export const LineHeight = {
  display: 40,
  h1: 36,
  h2: 32,
  h3: 28,
  heading: 20,
  body: 24,
  bodySmall: 22,
  label: 20,
  caption: 16,
  overline: 16,
  tiny: 14,
} as const;

export const FontWeight = {
  regular: "400" as const,
  medium: "500" as const,
  semiBold: "600" as const,
  bold: "700" as const,
};

export const Typography = {
  display: {
    fontSize: FontSize.display,
    lineHeight: LineHeight.display,
    fontWeight: FontWeight.bold,
  },
  h1: {
    fontSize: FontSize.h1,
    lineHeight: LineHeight.h1,
    fontWeight: FontWeight.bold,
  },
  h2: {
    fontSize: FontSize.h2,
    lineHeight: LineHeight.h2,
    fontWeight: FontWeight.semiBold,
  },
  h3: {
    fontSize: FontSize.h3,
    lineHeight: LineHeight.h3,
    fontWeight: FontWeight.semiBold,
  },
  heading: {
    fontSize: FontSize.heading,
    lineHeight: LineHeight.heading,
    fontWeight: FontWeight.semiBold,
  },
  body: {
    fontSize: FontSize.body,
    lineHeight: LineHeight.body,
    fontWeight: FontWeight.regular,
  },
  bodySmall: {
    fontSize: FontSize.bodySmall,
    lineHeight: LineHeight.bodySmall,
    fontWeight: FontWeight.regular,
  },
  label: {
    fontSize: FontSize.label,
    lineHeight: LineHeight.label,
    fontWeight: FontWeight.medium,
  },
  caption: {
    fontSize: FontSize.caption,
    lineHeight: LineHeight.caption,
    fontWeight: FontWeight.regular,
  },
  overline: {
    fontSize: FontSize.overline,
    lineHeight: LineHeight.overline,
    fontWeight: FontWeight.medium,
    textTransform: "uppercase" as const,
    letterSpacing: 0.8,
  },
  tiny: {
    fontSize: FontSize.tiny,
    lineHeight: LineHeight.tiny,
    fontWeight: FontWeight.regular,
  },
} as const;

export type TypographyVariant = keyof typeof Typography;

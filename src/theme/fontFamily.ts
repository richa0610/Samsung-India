import { Platform, type TextStyle } from "react-native";


export const APP_FONT_FAMILY: string | undefined = Platform.select({
  ios: "System",
  android: "sans-serif",
  default: undefined,
});

export const FontWeightValue = {
  thin: "100",
  light: "300",
  regular: "400",
  medium: "500",
  semiBold: "600",
  bold: "700",
  extraBold: "800",
  black: "900",
} as const satisfies Record<string, TextStyle["fontWeight"]>;

/**
 * @deprecated Legacy map — every entry now points at {@link APP_FONT_FAMILY}.
 * Kept only so existing `FontFamily.regular` imports keep compiling. New
 * code should use `AppText` with a `weight` prop instead.
 */
export const FontFamily = {
  thin: APP_FONT_FAMILY,
  light: APP_FONT_FAMILY,
  regular: APP_FONT_FAMILY,
  medium: APP_FONT_FAMILY,
  semiBold: APP_FONT_FAMILY,
  bold: APP_FONT_FAMILY,
  extraBold: APP_FONT_FAMILY,
  black: APP_FONT_FAMILY,
} as const;

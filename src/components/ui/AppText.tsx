import React from "react";
import { StyleSheet, Text, TextProps, TextStyle } from "react-native";

import { Colors } from "@/theme/colors";
import { APP_FONT_FAMILY, FontWeightValue } from "@/theme/fontFamily";
import {
  FontWeight,
  Typography,
  TypographyVariant,
} from "@/theme/typography";

export type TextWeight =
  | "300"
  | "400"
  | "500"
  | "600"
  | "700"
  | "800"
  | "900"
  | "light"
  | "regular"
  | "medium"
  | "semiBold"
  | "bold"
  | "extraBold"
  | "black";

const weightValueFor: Record<TextWeight, keyof typeof FontWeightValue> = {
  "300": "light",
  light: "light",
  "400": "regular",
  regular: "regular",
  "500": "medium",
  medium: "medium",
  "600": "semiBold",
  semiBold: "semiBold",
  "700": "bold",
  bold: "bold",
  "800": "extraBold",
  extraBold: "extraBold",
  "900": "black",
  black: "black",
};

export interface AppTextProps extends TextProps {
  children?: React.ReactNode;
  /** Semantic typography variant preset */
  variant?: TypographyVariant;
  /** @deprecated Use `variant` instead */
  size?: number;
  /** @deprecated Use `variant` instead */
  weight?: TextWeight;
  color?: string;
  align?: TextStyle["textAlign"];
}

export default function AppText({
  children,
  variant,
  size,
  weight,
  color = Colors.black,
  align,
  style,
  allowFontScaling = false,
  ...props
}: AppTextProps) {
  const preset = variant ? Typography[variant] : undefined;

  const resolvedSize = size ?? preset?.fontSize ?? Typography.body.fontSize;
  const resolvedLineHeight = preset?.lineHeight;
  const resolvedWeight = weight ?? preset?.fontWeight ?? FontWeight.regular;
  const resolvedLetterSpacing =
    preset && "letterSpacing" in preset ? preset.letterSpacing : undefined;
  const resolvedTextTransform =
    preset && "textTransform" in preset ? preset.textTransform : undefined;

  const resolvedFontWeight =
    FontWeightValue[weightValueFor[resolvedWeight] ?? "regular"];

  return (
    <Text
      allowFontScaling={allowFontScaling}
      style={[
        styles.text,
        {
          fontSize: resolvedSize,
          lineHeight: resolvedLineHeight,
          color,
          fontFamily: APP_FONT_FAMILY,
          fontWeight: resolvedFontWeight,
          letterSpacing: resolvedLetterSpacing,
          textTransform: resolvedTextTransform,
          textAlign: align,
        },
        style,
      ]}
      {...props}
    >
      {children}
    </Text>
  );
}

const styles = StyleSheet.create({
  text: {
    fontFamily: APP_FONT_FAMILY,
    includeFontPadding: false,
  },
});

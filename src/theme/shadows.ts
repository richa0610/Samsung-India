import { ViewStyle } from "react-native";
import { Colors } from "./colors";

type ShadowOptions = {
  x?: number;
  y?: number;
  blur?: number;
  spread?: number;
  color?: string;
  opacity?: number;
  elevation?: number;
};

function hexToRgb(hex: string): string {
  let c = hex.replace("#", "");
  if (c.length === 3)
    c = c
      .split("")
      .map((x) => x + x)
      .join("");
  const num = parseInt(c, 16);
  if (isNaN(num)) return "0, 0, 0";
  return `${(num >> 16) & 255}, ${(num >> 8) & 255}, ${num & 255}`;
}

export function createShadow({
  x = 0,
  y = 2,
  blur = 6,
  spread = 0,
  color = "#000000",
  opacity = 0.08,
  elevation = 2,
}: ShadowOptions = {}): ViewStyle {
  const isHex = color.startsWith("#");
  const colorStr = isHex ? `rgba(${hexToRgb(color)}, ${opacity})` : color;

  return {
    boxShadow: `${x}px ${y}px ${blur}px ${spread}px ${colorStr}`,
    elevation,
  } as ViewStyle;
}

export const Shadows = {
  card: createShadow({ x: 0, y: 2, blur: 6, opacity: 0.08, elevation: 2 }),
  timelineCard: createShadow({
    x: 0,
    y: 2,
    blur: 8,
    opacity: 0.06,
    elevation: 2,
  }),
  raised: createShadow({ x: 0, y: 3, blur: 8, opacity: 0.12, elevation: 5 }),
  homeButton: createShadow({
    x: 0,
    y: 4,
    blur: 10,
    color: Colors.headerBlue,
    opacity: 0.35,
    elevation: 8,
  }),
  footer: createShadow({ x: 0, y: -2, blur: 6, opacity: 0.08, elevation: 7 }),
  webContainer: createShadow({ x: 0, y: 0, blur: 24, opacity: 0.08, elevation: 4 }),
} as const;

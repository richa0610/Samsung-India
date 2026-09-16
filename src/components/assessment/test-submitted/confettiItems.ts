export type ConfettiItem = {
  top?: number;
  bottom?: number;
  left?: number;
  right?: number;
  color: string;
  rotate: string;
  width: number;
  height: number;
};

export const CONFETTI_ITEMS: ConfettiItem[] = [
  { top: 12, left: 34, color: "#F59E0B", rotate: "-15deg", width: 6, height: 10 },
  { top: 2, right: 65, color: "#10B981", rotate: "25deg", width: 6, height: 10 },
  { top: 22, right: 30, color: "#0EA5E9", rotate: "-35deg", width: 8, height: 8 },
  { top: 38, left: 52, color: "#0EA5E9", rotate: "45deg", width: 8, height: 8 },
  { top: 58, left: 24, color: "#10B981", rotate: "12deg", width: 7, height: 9 },
  { top: 46, right: 40, color: "#06B6D4", rotate: "-20deg", width: 6, height: 10 },
  { bottom: 6, left: 74, color: "#10B981", rotate: "30deg", width: 6, height: 9 },
  { bottom: 4, right: 48, color: "#F59E0B", rotate: "-25deg", width: 7, height: 9 },
  { top: 5, left: 72, color: "#10B981", rotate: "20deg", width: 6, height: 9 },
  { top: 6, right: 104, color: "#F59E0B", rotate: "-10deg", width: 5, height: 8 },
];

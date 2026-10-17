export function formatLeaderboardName(name: string): string {
  if (!name) return "";
  if (name.toUpperCase() === "YOU") return "You";
  return name
    .toLowerCase()
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Up to two capital letters from a person's name, for an avatar with no picture: "Pooja Sharma" ->
 * "PS", "anil" -> "A", "Pooja Kumari Sharma" -> "PK". Empty for a blank or missing name.
 */
export function initialsOf(name: string | null | undefined): string {
  return (name ?? "")
    .split(/\s+/)
    .filter(Boolean)
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

// Output-encoding guards for exportService.ts - each export format has its
// own injection risk from raw user-entered text, handled here so the format
// serializers in exportService.ts stay focused on structure, not escaping.

const FORMULA_TRIGGER_CHARS = ["=", "+", "-", "@"];

// Spreadsheet apps (Excel, Google Sheets, LibreOffice Calc) treat a cell
// starting with these characters as a formula - a value like
// `=cmd|'/c calc'!A1` can execute code when the exported file is opened.
// Prefixing with a single quote is the standard mitigation: it forces the
// cell to render as literal text instead of being evaluated.
export function sanitizeForSpreadsheet(value: string): string {
  return value && FORMULA_TRIGGER_CHARS.includes(value[0]) ? `'${value}` : value;
}

const HTML_ESCAPES: Record<string, string> = {
  "&": "&amp;",
  "<": "&lt;",
  ">": "&gt;",
  '"': "&quot;",
  "'": "&#39;",
};

export function escapeHtml(value: string): string {
  return value.replace(/[&<>"']/g, (char) => HTML_ESCAPES[char]);
}

import * as Clipboard from "expo-clipboard";
import { File, Paths } from "expo-file-system";
import * as Print from "expo-print";
import * as Sharing from "expo-sharing";
import * as XLSX from "xlsx";

import { escapeHtml, sanitizeForSpreadsheet } from "./exportSanitize";

export type ExportColumn = {
  key: string;
  header: string;
};

const sanitizeFileName = (name: string) => name.replace(/[^a-z0-9-_]+/gi, "_");

function cellText(value: unknown): string {
  if (value == null) return "";
  return String(value);
}

// Feeds CSV, TSV (clipboard) and Excel export - all three are opened in
// spreadsheet software, so every cell needs the formula-injection guard.
function toMatrix(columns: ExportColumn[], rows: Record<string, unknown>[]): string[][] {
  return [
    columns.map((column) => column.header),
    ...rows.map((row) => columns.map((column) => sanitizeForSpreadsheet(cellText(row[column.key])))),
  ];
}

function toCsv(columns: ExportColumn[], rows: Record<string, unknown>[]): string {
  const escapeCsvCell = (value: string) =>
    /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
  return toMatrix(columns, rows)
    .map((line) => line.map(escapeCsvCell).join(","))
    .join("\n");
}

function toTsv(columns: ExportColumn[], rows: Record<string, unknown>[]): string {
  return toMatrix(columns, rows)
    .map((line) => line.map((cell) => cell.replace(/\t/g, " ")).join("\t"))
    .join("\n");
}

function toHtmlTable(title: string, columns: ExportColumn[], rows: Record<string, unknown>[]): string {
  const headerHtml = columns.map((column) => `<th>${escapeHtml(column.header)}</th>`).join("");
  const rowsHtml = rows
    .map(
      (row) =>
        `<tr>${columns.map((column) => `<td>${escapeHtml(cellText(row[column.key]))}</td>`).join("")}</tr>`
    )
    .join("");
  return `
    <html>
      <head>
        <meta charset="utf-8" />
        <style>
          body { font-family: -apple-system, Roboto, Arial, sans-serif; padding: 16px; }
          h1 { font-size: 18px; margin-bottom: 12px; }
          table { width: 100%; border-collapse: collapse; }
          th, td { border: 1px solid #E5E7EB; padding: 6px 10px; font-size: 12px; text-align: left; }
          th { background: #F3F4F6; }
        </style>
      </head>
      <body>
        <h1>${escapeHtml(title)}</h1>
        <table>
          <thead><tr>${headerHtml}</tr></thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      </body>
    </html>
  `;
}

async function writeExportFile(fileName: string, content: string, encoding: "utf8" | "base64") {
  const file = new File(Paths.cache, fileName);
  if (file.exists) file.delete();
  file.create();
  file.write(content, { encoding });
  return file;
}

async function shareFile(file: File, mimeType: string, dialogTitle: string) {
  const available = await Sharing.isAvailableAsync();
  if (!available) {
    throw new Error("Sharing isn't available on this device.");
  }
  await Sharing.shareAsync(file.uri, { mimeType, dialogTitle });
}

export async function copyTableToClipboard(columns: ExportColumn[], rows: Record<string, unknown>[]) {
  await Clipboard.setStringAsync(toTsv(columns, rows));
}

export async function exportTableAsCsv(
  columns: ExportColumn[],
  rows: Record<string, unknown>[],
  fileName: string
) {
  const file = await writeExportFile(`${sanitizeFileName(fileName)}.csv`, toCsv(columns, rows), "utf8");
  await shareFile(file, "text/csv", "Export CSV");
}

export async function exportTableAsExcel(
  columns: ExportColumn[],
  rows: Record<string, unknown>[],
  fileName: string
) {
  const worksheet = XLSX.utils.aoa_to_sheet(toMatrix(columns, rows));
  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Sheet1");
  const base64 = XLSX.write(workbook, { type: "base64", bookType: "xlsx" }) as string;
  const file = await writeExportFile(`${sanitizeFileName(fileName)}.xlsx`, base64, "base64");
  await shareFile(
    file,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "Export Excel"
  );
}

export async function exportTableAsPdf(
  title: string,
  columns: ExportColumn[],
  rows: Record<string, unknown>[],
  fileName: string
) {
  const { uri } = await Print.printToFileAsync({ html: toHtmlTable(title, columns, rows) });
  const file = new File(uri);
  const target = new File(Paths.cache, `${sanitizeFileName(fileName)}.pdf`);
  if (target.exists) target.delete();
  await file.move(target);
  await shareFile(target, "application/pdf", "Export PDF");
}

export async function printTable(title: string, columns: ExportColumn[], rows: Record<string, unknown>[]) {
  await Print.printAsync({ html: toHtmlTable(title, columns, rows) });
}

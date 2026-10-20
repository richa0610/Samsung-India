import { StyleSheet } from "react-native";

import { Colors } from "@/theme/colors";

/** Base column widths (dp) of the Participant Master List. Each is just wide enough for its
 *  content (a long name ends in "..."), so the columns sit close together; on a phone the table
 *  scrolls sideways for the rest. There's no audience column: the audience type is a short tag
 *  (ASN / UASN / FRESH) under the phone number in the details column. */
export const PARTICIPANT_COLUMNS = {
  details: 88,
  stage: 88,
  status: 50,
  inOut: 62,
  score: 50,
  controls: 80,
} as const;

export type ParticipantColumn = keyof typeof PARTICIPANT_COLUMNS;
export type ColumnWidths = Record<ParticipantColumn, number>;

/** The heading bar's border, which sits inside its width. */
export const HEADER_BORDER_WIDTH = 1;
/** No padding at either end of a row - only the width of the heading bar's border, so a data row's
 *  cells start exactly where the heading's do (just inside that border) and the columns line up.
 *  The heading row itself then has no side padding at all (ROW_SIDE_PADDING - HEADER_BORDER_WIDTH). */
export const ROW_SIDE_PADDING = HEADER_BORDER_WIDTH;

const BASE_TOTAL = Object.values(PARTICIPANT_COLUMNS).reduce((sum, width) => sum + width, 0);

/** The table's narrowest width: every column at its base width, plus the rows' side padding. */
export const PARTICIPANT_TABLE_MIN_WIDTH = BASE_TOTAL + ROW_SIDE_PADDING * 2;

/** The columns' widths for a table area `availableWidth` wide: the base widths on a phone (the
 *  table then scrolls sideways), all stretched by the same factor to fill a wider screen. Plain
 *  fixed widths - the same numbers for the heading and every row - so a column stays put whatever
 *  is in it (a long name or "Not Started" can't push the next columns along). */
export function columnWidths(availableWidth: number): ColumnWidths {
  const scale = Math.max(1, (availableWidth - ROW_SIDE_PADDING * 2) / BASE_TOTAL);
  return Object.fromEntries(
    Object.entries(PARTICIPANT_COLUMNS).map(([column, width]) => [column, Math.floor(width * scale)]),
  ) as ColumnWidths;
}

/** Every cell of the list - header and rows alike - is a flex box centring its content both ways
 *  (justifyContent / alignItems: center). Its side padding is the gap between columns. */
export const participantCell = StyleSheet.create({
  cell: { justifyContent: "center", alignItems: "center", paddingHorizontal: 2 },
}).cell;

/** The Participant Details column, heading and rows: left-aligned (a small inset keeps it clear of
 *  the heading bar's rounded corner), and frozen while the rest of the table scrolls sideways - it
 *  is drawn above the other cells (zIndex) with a divider on its right, and the card shifts it by
 *  exactly the scroll distance, so it stays put on screen. Each user gives it its own background
 *  (its row's colour), so nothing scrolling underneath shows through. */
export const DETAILS_INSET = 6;
export const frozenDetailsCell = StyleSheet.create({
  cell: {
    alignItems: "flex-start",
    paddingLeft: DETAILS_INSET,
    zIndex: 1,
    borderRightWidth: 1,
    borderRightColor: Colors.gray200,
  },
}).cell;

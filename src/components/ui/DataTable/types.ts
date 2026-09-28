import { ReactNode } from "react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  minWidth?: number;
  render?: (row: T, index: number) => ReactNode;
  exportValue?: (row: T, index: number) => string;
  searchValue?: (row: T) => string;
  sortable?: boolean;
};

export type DataTablePageSize = number | "all";

/** Server-driven mode: the server does the searching, sorting and paging, so the
 *  table only ever holds the rows loaded so far and asks for more as you scroll. */
export type DataTableServerMode<T> = {
  /** All rows matching the current search / filters (null until page 1 arrives). */
  total: number | null;
  /** Current page (1-based) and the rows per page; `data` holds just this page. */
  page: number;
  pageSize: number;
  pageSizeOptions: number[];
  onPageChange: (page: number) => void;
  /** Rows per page; the owner sends the chosen size to the server as the page limit. */
  onPageSizeChange: (size: number) => void;
  search: string;
  onSearchChange: (value: string) => void;
  sort: { key: string; direction: "asc" | "desc" } | null;
  /** Called with a column key; the owner cycles asc -> desc -> none. */
  onSortChange: (key: string) => void;
  /** Only these columns can be sorted (the ones the server knows how to sort by). */
  sortableKeys: ReadonlySet<string>;
  /** Fetches every matching row (all pages) for export / copy / print. */
  onExportAll: () => Promise<T[]>;
};

export type ExportAction = "copy" | "csv" | "excel" | "pdf" | "print";

export type DataTableToolbarVariant = "full" | "download";

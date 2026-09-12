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

export type ExportAction = "copy" | "csv" | "excel" | "pdf" | "print";

export type DataTableToolbarVariant = "full" | "download";

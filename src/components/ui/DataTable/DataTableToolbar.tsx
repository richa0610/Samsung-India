import { Ionicons, MaterialCommunityIcons } from "@expo/vector-icons";
import { useState } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  TextInput,
  View,
} from "react-native";

import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { Spacing } from "@/theme/spacing";
import { DataTablePageSize, ExportAction } from "./types";

type ToolbarColumn = { key: string; header: string };

type DataTableToolbarProps = {
  pageSize: DataTablePageSize;
  pageSizeOptions: DataTablePageSize[];
  onPageSizeChange: (size: DataTablePageSize) => void;
  search: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder: string;
  columns: ToolbarColumn[];
  hiddenColumns: Set<string>;
  onToggleColumn: (key: string) => void;
  onCopy: () => void;
  onExportCsv: () => void;
  onExportExcel: () => void;
  onExportPdf: () => void;
  onPrint: () => void;
  busyAction: ExportAction | null;
  searchLoading?: boolean;
};

export default function DataTableToolbar({
  pageSize,
  pageSizeOptions,
  onPageSizeChange,
  search,
  onSearchChange,
  searchPlaceholder,
  columns,
  hiddenColumns,
  onToggleColumn,
  onCopy,
  onExportCsv,
  onExportExcel,
  onExportPdf,
  onPrint,
  busyAction,
  searchLoading = false,
}: DataTableToolbarProps) {
  const [openMenu, setOpenMenu] = useState<"pageSize" | "columns" | null>(null);
  const [inputValue, setInputValue] = useState(search);
  // Follow the `search` prop when the owner changes it (e.g. a reset): adjusted during render
  // against the last value seen, rather than in an effect that would render twice.
  const [syncedSearch, setSyncedSearch] = useState(search);
  if (search !== syncedSearch) {
    setSyncedSearch(search);
    setInputValue(search);
  }

  const handleSearch = () => {
    onSearchChange(inputValue.trim());
  };

  const pageSizeLabel = pageSize === "all" ? "Show all rows" : `Show ${pageSize} rows`;

  return (
    <View style={styles.container}>
      <View style={styles.row}>
        <ToolbarButton
          icon="copy-outline"
          label="Copy"
          onPress={onCopy}
          iconColor={Colors.copyIconColour}
          busy={busyAction === "copy"}
        />
        <ToolbarButton
          icon="document-text-outline"
          label="CSV"
          iconColor={Colors.csvIconColour}
          onPress={onExportCsv}
          busy={busyAction === "csv"}
        />
        <ToolbarButton
          icon="microsoft-excel"
          iconFamily="material-community"
          label="Excel"
          iconColor={Colors.excelIconColour}
          onPress={onExportExcel}
          busy={busyAction === "excel"}
        />
        <ToolbarButton
          icon="document-text-outline"
          label="PDF"
          onPress={onExportPdf}
          busy={busyAction === "pdf"}
          tone="danger"
        />
        <ToolbarButton
          icon="print-outline"
          label="Print"
          onPress={onPrint}
          iconColor={Colors.copyIconColour}
          busy={busyAction === "print"}
        />
      </View>

      <View style={styles.row}>
        <View style={styles.dropdownWrap}>
          <Pressable
            style={styles.dropdownTrigger}
            onPress={() =>
              setOpenMenu((current) =>
                current === "pageSize" ? null : "pageSize",
              )
            }
          >
            <AppText style={styles.dropdownTriggerText} numberOfLines={1}>
              {pageSizeLabel}
            </AppText>
            <Ionicons
              name={openMenu === "pageSize" ? "chevron-up" : "chevron-down"}
              size={13}
              color={Colors.gray600}
            />
          </Pressable>
          {openMenu === "pageSize" && (
            <View style={styles.dropdownPanel}>
              {pageSizeOptions.map((option) => (
                <Pressable
                  key={String(option)}
                  style={styles.dropdownItem}
                  onPress={() => {
                    onPageSizeChange(option);
                    setOpenMenu(null);
                  }}
                >
                  <AppText
                    style={styles.dropdownItemText}
                    color={
                      option === pageSize ? Colors.mainColour1 : Colors.black
                    }
                    weight={
                      option === pageSize
                        ? FontWeight.semiBold
                        : FontWeight.medium
                    }
                  >
                    {option === "all" ? "All rows" : `${option} rows`}
                  </AppText>
                </Pressable>
              ))}
            </View>
          )}
        </View>

        <View style={styles.dropdownWrap}>
          <Pressable
            style={[styles.dropdownTrigger, styles.columnTrigger]}
            onPress={() =>
              setOpenMenu((current) =>
                current === "columns" ? null : "columns",
              )
            }
          >
            <Ionicons
              name="eye-outline"
              size={14}
              color={Colors.copyIconColour}
            />
            <AppText style={styles.dropdownTriggerText} numberOfLines={1}>
              Column visibility
            </AppText>
            <Ionicons
              name={openMenu === "columns" ? "chevron-up" : "chevron-down"}
              size={13}
              color={Colors.gray600}
            />
          </Pressable>
        </View>

        <View style={styles.searchWrap}>
          <View style={styles.searchBox}>
            <Ionicons name="search" size={12} color={Colors.gray400} />
            <TextInput
              style={styles.searchInput}
              placeholder={searchPlaceholder}
              placeholderTextColor={Colors.gray400}
              value={inputValue}
              onChangeText={setInputValue}
              returnKeyType="search"
              onSubmitEditing={handleSearch}
            />
            {inputValue.length > 0 && (
              <Pressable
                onPress={() => {
                  setInputValue("");
                  onSearchChange("");
                }}
                hitSlop={6}
                accessibilityRole="button"
                accessibilityLabel="Clear search"
              >
                <Ionicons name="close-circle" size={14} color={Colors.gray400} />
              </Pressable>
            )}
          </View>
          <Pressable
            style={[styles.searchButton, searchLoading && styles.searchButtonDisabled]}
            onPress={searchLoading ? undefined : handleSearch}
            disabled={searchLoading}
            accessibilityRole="button"
            accessibilityLabel="Search"
          >
            {searchLoading ? (
              <ActivityIndicator size="small" color={Colors.white} style={styles.searchLoader} />
            ) : (
              <Ionicons name="search" size={12} color={Colors.white} />
            )}
            <AppText style={styles.searchButtonText} color={Colors.white} weight={FontWeight.semiBold}>
              Search
            </AppText>
          </Pressable>
        </View>
      </View>

      <AppModal
        visible={openMenu === "columns"}
        onClose={() => setOpenMenu(null)}
        position="bottom"
        title="Column Visibility"
        showCloseButton
        contentStyle={styles.columnSheet}
      >
        <ScrollView style={styles.columnScroll} showsVerticalScrollIndicator keyboardShouldPersistTaps="handled">
          {columns.map((column) => {
            const hidden = hiddenColumns.has(column.key);
            return (
              <Pressable
                key={column.key}
                style={styles.columnRow}
                onPress={() => onToggleColumn(column.key)}
              >
                <Ionicons
                  name={hidden ? "square-outline" : "checkbox"}
                  size={16}
                  color={hidden ? Colors.gray400 : Colors.mainColour1}
                />
                <AppText
                  style={styles.columnRowText}
                  color={hidden ? Colors.gray600 : Colors.black}
                >
                  {column.header}
                </AppText>
              </Pressable>
            );
          })}
        </ScrollView>
      </AppModal>
    </View>
  );
}

function ToolbarButton({
  icon,
  iconFamily = "ionicons",
  label,
  onPress,
  busy,
  tone = "default",
  iconColor: iconColorOverride,
}: {
  icon:
    | keyof typeof Ionicons.glyphMap
    | keyof typeof MaterialCommunityIcons.glyphMap;
  iconFamily?: "ionicons" | "material-community";
  label: string;
  onPress: () => void;
  busy?: boolean;
  tone?: "default" | "success" | "danger";
  iconColor?: string;
}) {
  const toneStyle = tone === "success" ? styles.toolbarButtonSuccess : null;
  const textColor = tone === "success" ? Colors.white : Colors.gray600;
  const iconColor =
    iconColorOverride ?? (tone === "danger" ? Colors.danger : textColor);
  const IconComponent =
    iconFamily === "material-community" ? MaterialCommunityIcons : Ionicons;

  return (
    <Pressable
      style={[styles.toolbarButton, toneStyle]}
      onPress={onPress}
      disabled={busy}
      hitSlop={2}
    >
      {busy ? (
        <ActivityIndicator size="small" color={iconColor} />
      ) : (
        <>
          <IconComponent name={icon as never} size={13} color={iconColor} />
          <AppText
            style={styles.toolbarButtonText}
            color={textColor}
            weight={FontWeight.semiBold}
            numberOfLines={1}
          >
            {label}
          </AppText>
        </>
      )}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  container: { gap: 8, paddingBottom: 4 },
  row: { flexDirection: "row", alignItems: "center", gap: 6, flexWrap: "wrap" },

  toolbarButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 3,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.md,
    paddingHorizontal: 7,
    height: 32,
    backgroundColor: Colors.white,
    flexShrink: 1,
  },
  toolbarButtonSuccess: {
    backgroundColor: Colors.success,
    borderColor: Colors.success,
  },
  toolbarButtonText: { fontSize: Fonts.overline },

  dropdownWrap: { position: "relative", zIndex: 10, flexShrink: 1 },
  dropdownTrigger: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.md,
    paddingHorizontal: 17,
    height: 32,
    backgroundColor: Colors.white,
  },
  columnTrigger: { paddingHorizontal: 10 },
  dropdownTriggerText: { fontSize: Fonts.overline, flexShrink: 1 },
  dropdownPanel: {
    position: "absolute",
    top: 36,
    left: 0,
    textAlign: "center",
    minWidth: 95,
    backgroundColor: Colors.white,
    borderRadius: Radius.md,
    paddingVertical: 4,
    ...Shadows.raised,
  },
  columnSheet: { paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xl, paddingTop: Spacing.sm },
  columnScroll: { maxHeight: 320 },
  columnRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingVertical: 13,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.lg,
  },
  columnRowText: { fontSize: Fonts.body },
  dropdownItem: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  dropdownItemText: { fontSize: Fonts.overline },

  searchWrap: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginLeft: "auto",
  },
  searchBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.md,
    paddingHorizontal: 8,
    height: 32,
    minWidth: 85,
    backgroundColor: Colors.white,
  },
  searchInput: {
    flex: 1,
    fontSize: Fonts.overline,
    color: Colors.black,
    padding: 0,
    minWidth: 50,
  },
  searchButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
    backgroundColor: Colors.mainColour1,
    borderRadius: Radius.md,
    paddingHorizontal: 10,
    height: 32,
  },
  searchButtonText: {
    fontSize: Fonts.overline,
    color: Colors.white,
  },
  searchLoader: {
    transform: [{ scale: 0.75 }],
  },
  searchButtonDisabled: {
    opacity: 0.82,
  },
});

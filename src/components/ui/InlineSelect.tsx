import { ReactNode, useMemo, useState } from "react";
import { Pressable, ScrollView, StyleSheet, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";

export type InlineOption = { label: string; value: string };

type InlineSelectProps = {
  placeholder?: string;
  value: string;
  options: InlineOption[];
  onSelect: (value: string) => void;
  disabled?: boolean;
  /** Show a filter box above the list once there are more than this many options. */
  searchAfter?: number;
};

/**
 * A tap-to-expand dropdown that reveals its options **inline** (no Modal), so
 * it works when rendered inside another Modal - e.g. the Edit Profile /
 * Register bottom sheets, where a native Picker dialog or a nested RN Modal
 * silently renders behind the sheet on Android.
 */
export default function InlineSelect({
  placeholder = "Select",
  value,
  options,
  onSelect,
  disabled,
  searchAfter = 8,
}: InlineSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const selected = options.find((o) => o.value === value);
  const showSearch = options.length > searchAfter;
  const filtered = useMemo(
    () =>
      showSearch && query
        ? options.filter((o) => o.label.toLowerCase().includes(query.toLowerCase()))
        : options,
    [options, query, showSearch],
  );

  return (
    <View style={styles.wrap}>
      <Pressable
        style={[styles.trigger, disabled && styles.triggerDisabled]}
        disabled={disabled}
        onPress={() => {
          setQuery("");
          setOpen((v) => !v);
        }}
        accessibilityRole="button"
      >
        <AppText
          style={styles.triggerText}
          color={selected || value ? Colors.black : Colors.gray400}
          numberOfLines={1}
        >
          {/* A saved value that doesn't match any option (e.g. real trainee
              data like "Male"/"Maharashtra" saved outside this app, where
              our option lists are lowercase slugs) still gets shown as-is -
              never silently swapped for the placeholder, which would make a
              genuinely-filled, correctly-locked field look empty. */}
          {selected?.label || value || placeholder}
        </AppText>
        <Ionicons
          name={disabled ? "lock-closed" : open ? "chevron-up" : "chevron-down"}
          size={16}
          color={Colors.gray600}
        />
      </Pressable>

      {open && !disabled && (
        <View style={styles.panel}>
          {showSearch && (
            <View style={styles.searchRow}>
              <Ionicons name="search" size={14} color={Colors.gray400} />
              <TextInput
                style={styles.searchInput}
                placeholder="Search..."
                placeholderTextColor={Colors.gray400}
                value={query}
                onChangeText={setQuery}
              />
            </View>
          )}
          <OptionsList longList={showSearch}>
            {filtered.map((option) => {
              const active = option.value === value;
              return (
                <Pressable
                  key={option.value}
                  style={[styles.row, active && styles.rowActive]}
                  onPress={() => {
                    onSelect(option.value);
                    setOpen(false);
                  }}
                >
                  <AppText style={styles.rowText} color={active ? Colors.white : Colors.black}>
                    {option.label}
                  </AppText>
                  {active && <Ionicons name="checkmark" size={15} color={Colors.white} />}
                </Pressable>
              );
            })}
            {filtered.length === 0 && (
              <AppText style={styles.empty} color={Colors.gray400}>
                No matches found.
              </AppText>
            )}
          </OptionsList>
        </View>
      )}
    </View>
  );
}

/**
 * A short list renders as a plain View - a non-scrolling ScrollView nested
 * inside the form's ScrollView can swallow the first tap on Android. A long
 * list (state picker) keeps the capped-height ScrollView.
 */
function OptionsList({ longList, children }: { longList: boolean; children: ReactNode }) {
  if (!longList) return <View>{children}</View>;
  return (
    <ScrollView style={styles.list} nestedScrollEnabled keyboardShouldPersistTaps="handled">
      {children}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  wrap: { width: "100%", marginBottom: Spacing.lg },
  trigger: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    height: 50,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    paddingHorizontal: Spacing.lg,
    backgroundColor: Colors.white,
  },
  triggerDisabled: { backgroundColor: Colors.gray100, opacity: 0.7 },
  triggerText: { fontSize: Fonts.xs, flex: 1 },
  panel: {
    marginTop: 6,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.lg,
    backgroundColor: Colors.white,
    overflow: "hidden",
  },
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: Spacing.md,
    height: 40,
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray200,
  },
  searchInput: { flex: 1, fontSize: Fonts.xs, color: Colors.black, padding: 0 },
  list: { maxHeight: 220 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 12,
    paddingHorizontal: Spacing.md,
  },
  rowActive: { backgroundColor: Colors.mainColour1 },
  rowText: { fontSize: Fonts.bodySm },
  empty: { textAlign: "center", paddingVertical: 20, fontSize: Fonts.bodySm },
});

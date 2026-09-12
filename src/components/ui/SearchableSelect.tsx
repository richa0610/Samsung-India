import { useMemo, useState } from "react";
import { Pressable, ScrollView, StyleProp, StyleSheet, TextInput, View, ViewStyle } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";
import AppModal from "@/components/ui/AppModal";

// `name` is optional - only pickers whose `label` isn't itself the plain
// display name (e.g. the trainer picker prefixes an employee ID onto
// `label`) set it, for callers that need the bare name rather than the
// display string.
export type SelectOption = { label: string; value: string; name?: string };

type SearchableSelectProps = {
  label?: string;
  required?: boolean;
  title?: string;
  placeholder?: string;
  value: string;
  options: SelectOption[];
  onSelect: (option: SelectOption) => void;
  icon?: keyof typeof Ionicons.glyphMap;
  disabled?: boolean;
  // Smaller height/padding for tight layouts like the sessions filter panel.
  compact?: boolean;
  containerStyle?: StyleProp<ViewStyle>;
};

export function SearchableSelect({
  label,
  required,
  title,
  placeholder = "Select",
  value,
  options,
  onSelect,
  icon,
  disabled,
  compact = false,
  containerStyle,
}: SearchableSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const selected = options.find((o) => o.value === value);
  const filtered = useMemo(
    () => options.filter((o) => o.label.toLowerCase().includes(query.toLowerCase())),
    [options, query]
  );

  return (
    <View style={[styles.field, containerStyle]}>
      {label && (
        <AppText style={styles.fieldLabel} weight={FontWeight.medium}>
          {label}
          {required ? " *" : ""}
        </AppText>
      )}
      <Pressable
        style={[styles.trigger, compact && styles.triggerCompact, disabled && styles.triggerDisabled]}
        disabled={disabled}
        onPress={() => {
          setQuery("");
          setOpen(true);
        }}
      >
        {icon && <Ionicons name={icon} size={compact ? 14 : 16} color={Colors.gray600} />}
        <AppText style={[styles.triggerText, compact && styles.triggerTextCompact]} color={selected ? Colors.black : Colors.gray400} numberOfLines={1}>
          {selected?.label ?? placeholder}
        </AppText>
        <Ionicons name="chevron-down" size={compact ? 14 : 16} color={Colors.gray600} />
      </Pressable>

      <AppModal
        visible={open}
        onClose={() => setOpen(false)}
        position="bottom"
        title={title ?? label}
        showCloseButton
        contentStyle={styles.sheet}
      >
        <View style={styles.searchRow}>
          <Ionicons name="search" size={16} color={Colors.gray400} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search..."
            placeholderTextColor={Colors.gray400}
            value={query}
            onChangeText={setQuery}
            autoFocus
          />
        </View>
        <ScrollView style={styles.list} keyboardShouldPersistTaps="handled">
          {filtered.map((option) => {
            const active = option.value === value;
            return (
              <Pressable
                key={option.value}
                style={[styles.row, active && styles.rowActive]}
                onPress={() => {
                  onSelect(option);
                  setOpen(false);
                }}
              >
                <AppText style={styles.rowText} color={active ? Colors.white : Colors.black}>
                  {option.label}
                </AppText>
                {active && <Ionicons name="checkmark" size={16} color={Colors.white} />}
              </Pressable>
            );
          })}
          {filtered.length === 0 && (
            <AppText style={styles.empty} color={Colors.gray400}>
              No matches found.
            </AppText>
          )}
        </ScrollView>
      </AppModal>
    </View>
  );
}

type SearchableMultiSelectProps = {
  label?: string;
  title?: string;
  placeholder?: string;
  values: string[];
  options: SelectOption[];
  onChange: (values: string[]) => void;
  // Smaller height/padding for tight layouts like dense multi-field forms.
  compact?: boolean;
};

export function SearchableMultiSelect({
  label,
  title,
  placeholder = "Select",
  values,
  options,
  onChange,
  compact = false,
}: SearchableMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const labelFor = (value: string) => options.find((o) => o.value === value)?.label ?? value;
  const filtered = useMemo(
    () => options.filter((o) => o.label.toLowerCase().includes(query.toLowerCase())),
    [options, query]
  );

  const toggle = (value: string) => {
    onChange(values.includes(value) ? values.filter((v) => v !== value) : [...values, value]);
  };

  return (
    <View style={styles.field}>
      {label && (
        <AppText style={styles.fieldLabel} weight={FontWeight.medium}>
          {label}
        </AppText>
      )}
      <Pressable
        style={[styles.trigger, compact && styles.triggerCompact]}
        onPress={() => {
          setQuery("");
          setOpen(true);
        }}
      >
        <AppText style={[styles.triggerText, compact && styles.triggerTextCompact]} color={values.length ? Colors.black : Colors.gray400} numberOfLines={1}>
          {values.length ? values.map(labelFor).join(", ") : placeholder}
        </AppText>
        <Ionicons name="chevron-down" size={compact ? 14 : 16} color={Colors.gray600} />
      </Pressable>

      {values.length > 0 && (
        <View style={styles.chipRow}>
          {values.map((item) => (
            <Pressable key={item} style={styles.chip} onPress={() => toggle(item)}>
              <AppText style={styles.chipLabel} color={Colors.mainColour1}>{labelFor(item)}</AppText>
              <Ionicons name="close" size={13} color={Colors.mainColour1} />
            </Pressable>
          ))}
        </View>
      )}

      <AppModal
        visible={open}
        onClose={() => setOpen(false)}
        position="bottom"
        title={title ?? label}
        showCloseButton
        contentStyle={styles.sheet}
      >
        <View style={styles.searchRow}>
          <Ionicons name="search" size={16} color={Colors.gray400} />
          <TextInput
            style={styles.searchInput}
            placeholder="Search..."
            placeholderTextColor={Colors.gray400}
            value={query}
            onChangeText={setQuery}
            autoFocus
          />
        </View>
        <ScrollView style={styles.list} keyboardShouldPersistTaps="handled">
          {filtered.map((option) => {
            const active = values.includes(option.value);
            return (
              <Pressable key={option.value} style={[styles.row, active && styles.rowActive]} onPress={() => toggle(option.value)}>
                <AppText style={styles.rowText} color={active ? Colors.white : Colors.black}>{option.label}</AppText>
                {active && <Ionicons name="checkmark" size={16} color={Colors.white} />}
              </Pressable>
            );
          })}
          {filtered.length === 0 && (
            <AppText style={styles.empty} color={Colors.gray400}>
              No matches found.
            </AppText>
          )}
        </ScrollView>
        <Pressable style={styles.doneButton} onPress={() => setOpen(false)}>
          <AppText color={Colors.white} weight={FontWeight.semiBold}>Done</AppText>
        </Pressable>
      </AppModal>
    </View>
  );
}

const styles = StyleSheet.create({
  field: { width: "100%", marginBottom: Spacing.lg },
  fieldLabel: { fontSize: Fonts.body, marginBottom: Spacing.sm },
  trigger: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    height: 50,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    paddingHorizontal: Spacing.lg,
    backgroundColor: Colors.white,
  },
  triggerDisabled: { backgroundColor: Colors.gray100, opacity: 0.7 },
  triggerCompact: { height: 38, paddingHorizontal: Spacing.md, gap: 6 },
  triggerText: { fontSize: Fonts.xs, flex: 1 },
  triggerTextCompact: { fontSize: 12 },
  sheet: { paddingHorizontal: Spacing.lg, paddingBottom: Spacing.xl, paddingTop: Spacing.sm },
  searchRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    paddingHorizontal: Spacing.lg,
    height: 44,
    marginBottom: Spacing.sm,
  },
  searchInput: { flex: 1, fontSize: Fonts.xs, color: Colors.black },
  list: { maxHeight: 320 },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 13,
    paddingHorizontal: Spacing.md,
    borderRadius: Radius.lg,
  },
  rowActive: { backgroundColor: Colors.mainColour1 },
  rowText: { fontSize: Fonts.body },
  empty: { textAlign: "center", paddingVertical: 24, fontSize: Fonts.bodySm },
  chipRow: { flexDirection: "row", flexWrap: "wrap", gap: 8, marginTop: Spacing.sm },
  chip: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: Radius.pill,
    backgroundColor: "#E8F1FF",
  },
  chipLabel: { fontSize: Fonts.bodySm },
  doneButton: {
    marginTop: Spacing.sm,
    height: 46,
    borderRadius: Radius.xl,
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    justifyContent: "center",
  },
});

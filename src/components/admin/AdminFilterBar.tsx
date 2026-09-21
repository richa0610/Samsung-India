import { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { AdminFilters, defaultAdminFilters } from "@/api/adminFilters";
import { fetchSessionTypes, fetchTrainers, fetchTrainingTypes } from "@/api/training";
import { REGIONS_BY_ZONE, ZONES } from "@/components/training/add-training/constants";
import { MonthCard, useMonthYear } from "@/components/calendar/date-range";
import { MONTH_NAMES } from "@/components/calendar/calendarUtils";
import { formatDate, displayDate } from "@/components/training/add-training/formatting";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { SearchableMultiSelect, SelectOption } from "@/components/ui/SearchableSelect";
import { AdminFilterScope, useAdminFilters } from "@/hooks/useAdminFilters";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";

// The trainer calendar cards are built at ~146dp wide (7 day-cells of 18.5dp per
// row) - any wider and the grid wraps into 14 columns. So the popup renders one at
// that natural size and scales it up, which keeps it compact and fully readable.
const CARD_WIDTH = 146;
const CARD_HEIGHT = 205;
const CARD_SCALE = 1.5;

const toDate = (value: string): Date | null => {
  const [y, m, d] = value.split("-").map(Number);
  return y && m && d ? new Date(y, m - 1, d) : null;
};

// "02 Jul 26 - 21 Sep 2026" - short year on the From side, full year on the To side.
function formatRange(start: string, end: string): string | null {
  const from = toDate(start);
  const to = toDate(end);
  if (!from || !to) return null;
  const part = (d: Date, fullYear: boolean) =>
    `${String(d.getDate()).padStart(2, "0")} ${MONTH_NAMES[d.getMonth()]} ${fullYear ? d.getFullYear() : String(d.getFullYear()).slice(2)}`;
  return `${part(from, false)} - ${part(to, true)}`;
}

const asOptions = (values: string[]): SelectOption[] => values.map((value) => ({ label: value, value }));

/** "Select Range" toggle + collapsible filter panel for the admin pages. The
 *  dashboard ("home") has its own filter; the Training and Attendance lists share one. */
export default function AdminFilterBar({
  scope = "lists",
  dateOnly = false,
}: {
  scope?: AdminFilterScope;
  /** Only the From/To range (the trainee dashboard has nothing else to filter by). */
  dateOnly?: boolean;
}) {
  const { adminToken } = useAuth();
  const { applied, apply, clear } = useAdminFilters(scope);
  const [open, setOpen] = useState(false);
  const [pickerFor, setPickerFor] = useState<"start" | "end" | null>(null);
  const [draft, setDraft] = useState<AdminFilters>(applied);
  const [trainerOptions, setTrainerOptions] = useState<SelectOption[]>([]);
  const [sessionTypeOptions, setSessionTypeOptions] = useState<SelectOption[]>([]);
  const [trainingTypeOptions, setTrainingTypeOptions] = useState<SelectOption[]>([]);

  useEffect(() => {
    if (!open || !adminToken) return;
    fetchTrainers(adminToken).then(setTrainerOptions).catch(() => setTrainerOptions([]));
    fetchSessionTypes(adminToken).then(setSessionTypeOptions).catch(() => setSessionTypeOptions([]));
    fetchTrainingTypes(adminToken).then(setTrainingTypeOptions).catch(() => setTrainingTypeOptions([]));
  }, [open, adminToken]);

  const today = useMemo(() => new Date(), []);
  const todayStart = useMemo(() => new Date(today.getFullYear(), today.getMonth(), today.getDate()).getTime(), [today]);
  const startDate = toDate(draft.start);
  const endDate = toDate(draft.end);
  const fromMonthYear = useMonthYear(startDate ?? today);
  const toMonthYear = useMonthYear(endDate ?? today);

  const regionOptions = useMemo(() => {
    const zones = draft.zones.length ? draft.zones : ZONES;
    return asOptions(Array.from(new Set(zones.flatMap((zone) => REGIONS_BY_ZONE[zone] ?? []))));
  }, [draft.zones]);

  const toggle = () => {
    if (!open) setDraft(applied);
    setPickerFor(null);
    setOpen((value) => !value);
  };

  const handleApply = () => {
    // A half-picked range defaults the missing side to today (From is never after
    // today and To never before it, so the result is always a valid range).
    const todayText = formatDate(today);
    let { start, end } = draft;
    if (start && !end) end = todayText;
    if (end && !start) start = todayText;
    const next = { ...draft, start, end };
    setDraft(next);
    apply(next);
    setOpen(false);
  };

  const handleClear = () => {
    clear();
    setDraft(defaultAdminFilters());
    setOpen(false);
  };

  const rangeLabel = formatRange(applied.start, applied.end);

  return (
    <View style={styles.wrap}>
      <Pressable style={styles.toggle} onPress={toggle} accessibilityRole="button" accessibilityLabel="Select Range">
        <Ionicons name="calendar" size={14} color={Colors.white} />
        <AppText style={styles.toggleText} color={Colors.white} weight={FontWeight.semiBold}>
          Select Range
        </AppText>
        {rangeLabel && (
          <View style={styles.rangeChip}>
            <AppText style={styles.rangeChipText} weight={FontWeight.bold}>
              {rangeLabel}
            </AppText>
          </View>
        )}
        <Ionicons name={open ? "chevron-up" : "chevron-down"} size={14} color={Colors.white} />
      </Pressable>

      {open && (
        <View style={styles.panel}>
          <View style={styles.dateRow}>
            {(["start", "end"] as const).map((key) => (
              <View key={key} style={styles.dateCell}>
                <AppText style={styles.fieldLabel} weight={FontWeight.medium}>
                  {key === "start" ? "From Date:" : "To Date:"}
                </AppText>
                <Pressable
                  style={styles.dateBox}
                  onPress={() => setPickerFor(key)}
                  accessibilityRole="button"
                  accessibilityLabel={key === "start" ? "Select from date" : "Select to date"}
                >
                  <Ionicons name="calendar-outline" size={14} color={Colors.gray600} />
                  <AppText style={styles.dateText} color={draft[key] ? Colors.black : Colors.gray400}>
                    {draft[key] ? displayDate(draft[key]) : "Select Date"}
                  </AppText>
                </Pressable>
              </View>
            ))}
          </View>

          {!dateOnly && (
            <>
          <View style={styles.pairRow}>
            <View style={styles.pairCell}>
              <SearchableMultiSelect
                compact
                label="Trainer:"
                placeholder="Select"
                values={draft.trainers}
                options={trainerOptions}
                onChange={(trainers) => setDraft({ ...draft, trainers })}
              />
            </View>
            <View style={styles.pairCell}>
              <SearchableMultiSelect
                compact
                label="Zone:"
                placeholder="Select"
                values={draft.zones}
                options={asOptions(ZONES)}
                onChange={(zones) => setDraft({ ...draft, zones, regions: [] })}
              />
            </View>
          </View>
          <View style={styles.pairRow}>
            <View style={styles.pairCell}>
              <SearchableMultiSelect
                compact
                label="Region:"
                placeholder="Select"
                values={draft.regions}
                options={regionOptions}
                onChange={(regions) => setDraft({ ...draft, regions })}
              />
            </View>
            <View style={styles.pairCell}>
              <SearchableMultiSelect
                compact
                label="Session Type:"
                placeholder="Select"
                values={draft.sessionTypes}
                options={sessionTypeOptions}
                onChange={(sessionTypes) => setDraft({ ...draft, sessionTypes })}
              />
            </View>
          </View>
          <SearchableMultiSelect
            compact
            label="Training Type:"
            placeholder="Select"
            values={draft.trainingTypes}
            options={trainingTypeOptions}
            onChange={(trainingTypes) => setDraft({ ...draft, trainingTypes })}
          />

            </>
          )}

          <View style={styles.buttonRow}>
            <Pressable style={[styles.button, styles.applyButton]} onPress={handleApply} accessibilityRole="button">
              <AppText color={Colors.white} weight={FontWeight.semiBold} style={styles.buttonText}>
                Filter View
              </AppText>
            </Pressable>
            <Pressable style={[styles.button, styles.clearButton]} onPress={handleClear} accessibilityRole="button">
              <AppText color={Colors.gray600} weight={FontWeight.semiBold} style={styles.buttonText}>
                Clear
              </AppText>
            </Pressable>
          </View>
        </View>
      )}

      {/* One calendar at a time, in a popup - FROM or TO depending on which box was tapped. */}
      <AppModal visible={pickerFor !== null} onClose={() => setPickerFor(null)} position="center" closeOnOverlayPress>
        <View style={styles.pickerCard}>
          <View style={styles.scaleBox}>
            <View style={styles.scaleInner}>
          {pickerFor === "start" && (
            <MonthCard
              title="FROM :"
              summaryLabel="From Date"
              monthYear={fromMonthYear}
              selectedStart={startDate ?? new Date(0)}
              selectedEnd={startDate ?? new Date(0)}
              summaryDate={startDate ?? today}
              onSelectDate={(date) => {
                setDraft({ ...draft, start: formatDate(date) });
                setPickerFor(null);
              }}
              onClear={() => {
                setDraft({ ...draft, start: "" });
                setPickerFor(null);
              }}
              // From can't be after today (or after the To date).
              isDateDisabled={(date) => date.getTime() > todayStart || (!!endDate && date.getTime() > endDate.getTime())}
            />
          )}
          {pickerFor === "end" && (
            <MonthCard
              title="TO :"
              summaryLabel="To Date"
              monthYear={toMonthYear}
              selectedStart={endDate ?? new Date(0)}
              selectedEnd={endDate ?? new Date(0)}
              summaryDate={endDate ?? today}
              onSelectDate={(date) => {
                setDraft({ ...draft, end: formatDate(date) });
                setPickerFor(null);
              }}
              onClear={() => {
                setDraft({ ...draft, end: "" });
                setPickerFor(null);
              }}
              // To can't be before today (or before the From date).
              isDateDisabled={(date) => date.getTime() < todayStart || (!!startDate && date.getTime() < startDate.getTime())}
            />
          )}
            </View>
          </View>
        </View>
      </AppModal>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: 8, marginBottom: 8 },
  toggle: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "flex-start",
    gap: 6,
    backgroundColor: "#2F44C5",
    borderRadius: Radius.lg,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  toggleText: { fontSize: Fonts.overline },
  rangeChip: { backgroundColor: Colors.white, borderRadius: Radius.pill, paddingHorizontal: 8, paddingVertical: 2 },
  rangeChipText: { fontSize: 10, color: "#2F44C5" },
  panel: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xxxl,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    paddingHorizontal: 10,
    paddingTop: 10,
    paddingBottom: 6,
    ...Shadows.card,
  },
  dateRow: { flexDirection: "row", gap: 8 },
  dateCell: { flex: 1 },
  fieldLabel: { fontSize: Fonts.body, marginBottom: 4 },
  dateBox: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    height: 38,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    paddingHorizontal: 10,
    backgroundColor: Colors.white,
    marginBottom: 8,
  },
  dateText: { fontSize: 12, flex: 1 },
  pickerCard: { padding: 8, backgroundColor: Colors.white, borderRadius: 16 },
  scaleBox: { width: CARD_WIDTH * CARD_SCALE, height: CARD_HEIGHT * CARD_SCALE },
  // MonthCard is `flex: 1`, so it needs a parent with a real height or it collapses.
  scaleInner: {
    position: "absolute",
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
    left: (CARD_WIDTH * CARD_SCALE - CARD_WIDTH) / 2,
    top: (CARD_HEIGHT * CARD_SCALE - CARD_HEIGHT) / 2,
    transform: [{ scale: CARD_SCALE }],
  },
  pairRow: { flexDirection: "row", gap: 8 },
  pairCell: { flex: 1 },
  buttonRow: { flexDirection: "row", gap: 8, marginTop: 0, marginBottom: 4 },
  button: { flex: 1, height: 36, borderRadius: Radius.lg, alignItems: "center", justifyContent: "center" },
  applyButton: { backgroundColor: "#16A34A" },
  clearButton: { backgroundColor: Colors.gray100, borderWidth: 1, borderColor: Colors.gray200 },
  buttonText: { fontSize: Fonts.overline },
});

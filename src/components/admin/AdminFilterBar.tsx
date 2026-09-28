import { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import { AdminAccessScope, fetchAdminAccessScope } from "@/api/admin";
import { AdminFilters, EMPTY_ADMIN_FILTERS, defaultAdminFilters, monthToDateAdminFilters } from "@/api/adminFilters";
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
  // The caller's own admin_access grant (null until it's loaded, or for `dateOnly` bars that
  // never show zone/region at all) - narrows which zone/region options this account even sees.
  // Display only: the backend enforces the real boundary regardless of what's picked here.
  const [accessScope, setAccessScope] = useState<AdminAccessScope | null>(null);

  useEffect(() => {
    if (!open || !adminToken) return;
    fetchTrainers(adminToken).then(setTrainerOptions).catch(() => setTrainerOptions([]));
    fetchSessionTypes(adminToken).then(setSessionTypeOptions).catch(() => setSessionTypeOptions([]));
    fetchTrainingTypes(adminToken).then(setTrainingTypeOptions).catch(() => setTrainingTypeOptions([]));
    if (!dateOnly) fetchAdminAccessScope(adminToken).then(setAccessScope).catch(() => setAccessScope(null));
  }, [open, adminToken, dateOnly]);

  const today = useMemo(() => new Date(), []);
  const startDate = toDate(draft.start);
  const endDate = toDate(draft.end);
  const fromMonthYear = useMonthYear(startDate ?? today);
  const toMonthYear = useMonthYear(endDate ?? today);

  // `null` on either axis (Super Admin, Company Admin, or the scope hasn't loaded yet) means
  // "not restricted" - keep every zone/region option. A list narrows to just those.
  const zoneOptions = useMemo(() => {
    if (!accessScope?.zones) return ZONES;
    const allowed = new Set(accessScope.zones);
    return ZONES.filter((zone) => allowed.has(zone.trim().toLowerCase()));
  }, [accessScope]);

  const regionOptions = useMemo(() => {
    const zones = draft.zones.length ? draft.zones : zoneOptions;
    let regions = Array.from(new Set(zones.flatMap((zone) => REGIONS_BY_ZONE[zone] ?? [])));
    if (accessScope?.regions) {
      const allowed = new Set(accessScope.regions);
      regions = regions.filter((region) => allowed.has(region.trim().toLowerCase()));
    }
    return asOptions(regions);
  }, [draft.zones, zoneOptions, accessScope]);

  const toggle = () => {
    if (!open) {
      // The dashboard shows today by default; opening the panel while that default
      // is still applied pre-fills the current month (1st through today) instead.
      const todayText = formatDate(today);
      const isTodayDefault = scope === "home" && applied.start === todayText && applied.end === todayText;
      setDraft(isTodayDefault ? { ...applied, start: monthToDateAdminFilters().start } : applied);
    }
    setPickerFor(null);
    setOpen((value) => !value);
  };

  const handleApply = () => {
    // A half-picked range defaults the missing side to today, and a range picked
    // the wrong way round (From after To) is swapped so it's always valid.
    const todayText = formatDate(today);
    let { start, end } = draft;
    if (start && !end) end = todayText;
    if (end && !start) start = todayText;
    if (start > end) [start, end] = [end, start];
    const next = { ...draft, start, end };
    setDraft(next);
    apply(next);
    setOpen(false);
  };

  const handleClear = () => {
    clear();
    // Home goes back to today; other scopes reset to fully empty.
    setDraft(scope === "home" ? defaultAdminFilters() : EMPTY_ADMIN_FILTERS);
    setOpen(false);
  };

  const rangeLabel = formatRange(applied.start, applied.end);
  // Only the dashboard gets the big full-width bar; every other page gets a
  // smaller, content-hugging version of the same toggle.
  const compact = scope !== "home";

  // The compact toggle sits directly on the page's own blue banner, so it
  // needs to be white/light to actually stand out instead of blending in.
  const compactIconColor = Colors.toggleBlue;

  return (
    <View style={styles.wrap}>
      <Pressable
        style={[styles.toggle, compact && styles.toggleCompact]}
        onPress={toggle}
        accessibilityRole="button"
        accessibilityLabel="Select Range"
      >
        <Ionicons name="calendar" size={compact ? 13 : 16} color={compact ? compactIconColor : Colors.white} />
        <AppText
          style={[styles.toggleText, compact && styles.toggleTextCompact]}
          color={compact ? compactIconColor : Colors.white}
          weight={FontWeight.semiBold}
        >
          Select Range
        </AppText>
        {rangeLabel && (
          <View style={[styles.rangeChip, compact && styles.rangeChipCompact]}>
            <AppText style={[styles.rangeChipText, compact && styles.rangeChipTextCompact]} weight={FontWeight.bold}>
              {rangeLabel}
            </AppText>
          </View>
        )}
        {!compact && <View style={styles.toggleSpacer} />}
        <Ionicons name={open ? "chevron-up" : "chevron-down"} size={compact ? 13 : 16} color={compact ? compactIconColor : Colors.white} />
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
                options={asOptions(zoneOptions)}
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
  wrap: { width: "100%", alignSelf: "stretch", gap: 8, marginBottom: 8 },
  toggle: {
    flexDirection: "row",
    alignItems: "center",
    alignSelf: "stretch",
    width: "100%",
    gap: 8,
    backgroundColor: Colors.toggleBlue,
    borderRadius: Radius.xl,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  toggleCompact: {
    alignSelf: "flex-start",
    width: "auto",
    gap: 5,
    backgroundColor: Colors.white,
    borderRadius: Radius.lg,
    paddingHorizontal: 10,
    paddingVertical: 6,
    ...Shadows.card,
  },
  toggleText: { fontSize: Fonts.bodySm },
  toggleTextCompact: { fontSize: 11 },
  toggleSpacer: { flex: 1 },
  rangeChip: { backgroundColor: Colors.white, borderRadius: Radius.pill, paddingHorizontal: 10, paddingVertical: 3 },
  // The toggle itself is white in compact mode, so this pill needs its own
  // tint to stay visible against it.
  rangeChipCompact: { backgroundColor: "#E7EAFB", paddingHorizontal: 7, paddingVertical: 2 },
  rangeChipText: { fontSize: 11, color: Colors.toggleBlue },
  rangeChipTextCompact: { fontSize: 9.5 },
  panel: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xxxl,
    borderWidth: 1,
    borderColor: Colors.gray200,
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
  applyButton: { backgroundColor: Colors.success },
  clearButton: { backgroundColor: Colors.gray100, borderWidth: 1, borderColor: Colors.gray200 },
  buttonText: { fontSize: Fonts.overline },
});

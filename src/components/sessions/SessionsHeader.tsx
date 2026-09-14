import { useState } from "react";
import { Pressable, StyleSheet, TextInput, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { Ionicons } from "@expo/vector-icons";

import { SelectOption } from "@/components/ui/SearchableSelect";
import { Colors } from "@/theme/colors";
import SessionsFilterPanel from "./SessionsFilterPanel";
import { SessionFilters, SessionTab } from "./sessionsUtils";

type SessionsHeaderProps = {
  dateRangeText?: string;
  activeTab: SessionTab;
  onSelectTab: (tab: SessionTab) => void;
  onSearchChange?: (text: string) => void;
  filters: SessionFilters;
  onFiltersChange: (patch: Partial<SessionFilters>) => void;
  locationOptions: SelectOption[];
  sessionTypeOptions: SelectOption[];
};

export default function SessionsHeader({
  dateRangeText = "01 Jul - 31 Jul",
  activeTab,
  onSelectTab,
  onSearchChange,
  filters,
  onFiltersChange,
  locationOptions,
  sessionTypeOptions,
}: SessionsHeaderProps) {
  const [showSearchInput, setShowSearchInput] = useState(false);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [showCalendarPanel, setShowCalendarPanel] = useState(false);
  const [searchText, setSearchText] = useState("");

  const handleSearchToggle = () => {
    setShowFilterPanel(false);
    setShowCalendarPanel(false);
    setShowSearchInput((prev) => {
      const next = !prev;
      if (!next) {
        setSearchText("");
        onSearchChange?.("");
      }
      return next;
    });
  };

  const handleFilterToggle = () => {
    setShowSearchInput(false);
    setShowCalendarPanel(false);
    setShowFilterPanel((prev) => !prev);
  };

  const handleCalendarToggle = () => {
    setShowSearchInput(false);
    setShowFilterPanel(false);
    setShowCalendarPanel((prev) => !prev);
  };

  const handleTextChange = (val: string) => {
    setSearchText(val);
    onSearchChange?.(val);
  };

  return (
    <View style={styles.container}>
      {/* Top Row: Icon + Title/Subtitle + 3 Action Buttons */}
      <View style={styles.topRow}>
        <View style={styles.titleWithIcon}>
          <View style={styles.iconCircle}>
            <Ionicons name="school" size={24} color={Colors.white} />
          </View>
          <View style={styles.titleTextContainer}>
            <AppText style={styles.title}>Sessions</AppText>
            <AppText style={styles.dateRangeSubtitle}>{dateRangeText}</AppText>
          </View>
        </View>

        <View style={styles.actionsRow}>
          <Pressable
            style={[styles.actionBtn, showSearchInput && styles.actionBtnActive]}
            onPress={handleSearchToggle}
            hitSlop={6}
            accessibilityRole="button"
            accessibilityLabel="Search sessions"
          >
            <Ionicons name="search" size={17} color={Colors.white} />
          </Pressable>

          <Pressable
            style={[styles.actionBtn, showFilterPanel && styles.actionBtnActive]}
            onPress={handleFilterToggle}
            hitSlop={6}
            accessibilityRole="button"
            accessibilityLabel="Filter sessions"
          >
            <Ionicons name="filter" size={17} color={Colors.white} />
          </Pressable>

          <Pressable
            style={[styles.actionBtn, showCalendarPanel && styles.actionBtnActive]}
            onPress={handleCalendarToggle}
            hitSlop={6}
            accessibilityRole="button"
            accessibilityLabel="Calendar view"
          >
            <Ionicons name="calendar-outline" size={17} color={Colors.white} />
          </Pressable>
        </View>
      </View>

      {/* Expandable Search Card */}
      {showSearchInput && (
        <View style={styles.searchCard}>
          <AppText style={styles.searchLabel}>Search Sessions</AppText>
          <View style={styles.searchInputRow}>
            <Ionicons name="search" size={16} color="#9CA3AF" />
            <TextInput
              style={styles.searchInput}
              placeholder="Search by session, name, type, trainer"
              placeholderTextColor="#9CA3AF"
              value={searchText}
              onChangeText={handleTextChange}
              autoFocus
            />
            {searchText.length > 0 && (
              <Pressable onPress={() => handleTextChange("")} hitSlop={6}>
                <Ionicons name="close-circle" size={16} color="#9CA3AF" />
              </Pressable>
            )}
          </View>
        </View>
      )}

      {/* Expandable Filter Panel */}
      {showFilterPanel && (
        <SessionsFilterPanel
          filters={filters}
          onChange={onFiltersChange}
          locationOptions={locationOptions}
          sessionTypeOptions={sessionTypeOptions}
        />
      )}

      {/* Expandable Calendar (Date Range only) Panel */}
      {showCalendarPanel && (
        <SessionsFilterPanel
          filters={filters}
          onChange={onFiltersChange}
          locationOptions={locationOptions}
          sessionTypeOptions={sessionTypeOptions}
          variant="dateOnly"
        />
      )}

      {/* Tabs Segment: All Sessions | Today | Completed */}
      <View style={styles.tabSegmentContainer}>
        <Pressable
          style={[styles.tabButton, activeTab === "all" && styles.tabButtonActive]}
          onPress={() => onSelectTab("all")}
          accessibilityRole="tab"
          accessibilityState={{ selected: activeTab === "all" }}
        >
          <AppText
            style={[
              styles.tabText,
              activeTab === "all" && styles.tabTextActive,
            ]}
          >
            All Sessions
          </AppText>
        </Pressable>

        <Pressable
          style={[
            styles.tabButton,
            activeTab === "today" && styles.tabButtonActive,
          ]}
          onPress={() => onSelectTab("today")}
          accessibilityRole="tab"
          accessibilityState={{ selected: activeTab === "today" }}
        >
          <AppText
            style={[
              styles.tabText,
              activeTab === "today" && styles.tabTextActive,
            ]}
          >
            Today
          </AppText>
        </Pressable>

        <Pressable
          style={[
            styles.tabButton,
            activeTab === "completed" && styles.tabButtonActive,
          ]}
          onPress={() => onSelectTab("completed")}
          accessibilityRole="tab"
          accessibilityState={{ selected: activeTab === "completed" }}
        >
          <AppText
            style={[
              styles.tabText,
              activeTab === "completed" && styles.tabTextActive,
            ]}
          >
            Completed
          </AppText>
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.mainColour1,
    paddingHorizontal: 16,
    paddingTop: 12,
    paddingBottom: 16,
    borderBottomLeftRadius: 20,
    borderBottomRightRadius: 20,
  },
  topRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
  },
  titleWithIcon: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  iconCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  titleTextContainer: {
    gap: 1,
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: Colors.white,
  },
  dateRangeSubtitle: {
    fontSize: 11.5,
    color: "rgba(255, 255, 255, 0.85)",
    fontWeight: "500",
  },
  actionsRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 14,
  },
  actionBtn: {
    width: 36,
    height: 36,
    borderRadius: 9,
    backgroundColor: "rgba(255, 255, 255, 0.18)",
    alignItems: "center",
    justifyContent: "center",
  },
  actionBtnActive: {
    backgroundColor: "rgba(255, 255, 255, 0.35)",
  },
  searchCard: {
    backgroundColor: Colors.white,
    borderRadius: 14,
    paddingHorizontal: 14,
    paddingVertical: 12,
    marginTop: 12,
  },
  searchLabel: {
    fontSize: 10.5,
    fontWeight: "700",
    color: "#9CA3AF",
    letterSpacing: 0.6,
    textTransform: "uppercase",
    marginBottom: 8,
  },
  searchInputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  searchInput: {
    flex: 1,
    fontSize: 13,
    color: "#111827",
    padding: 0,
  },
  tabSegmentContainer: {
    flexDirection: "row",
    backgroundColor: "rgba(0, 70, 180, 0.7)",
    borderRadius: 14,
    padding: 4,
    marginTop: 16,
  },
  tabButton: {
    flex: 1,
    paddingVertical: 9,
    alignItems: "center",
    justifyContent: "center",
    borderRadius: 10,
  },
  tabButtonActive: {
    backgroundColor: Colors.white,
  },
  tabText: {
    fontSize: 12.5,
    fontWeight: "600",
    color: "rgba(255, 255, 255, 0.9)",
  },
  tabTextActive: {
    color: Colors.mainColour1,
    fontWeight: "700",
  },
});

import { ReactNode } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

export type DashboardTab = "home" | "plan" | "today" | "profile" | "more";

type DashboardBottomNavProps = {
  activeTab: DashboardTab;
  onSelectTab: (tab: DashboardTab) => void;
};

export default function DashboardBottomNav({
  activeTab = "home",
  onSelectTab,
}: DashboardBottomNavProps) {
  const insets = useSafeAreaInsets();
  const tabs: {
    key: DashboardTab;
    label: string;
    isCenter?: boolean;
    icon: (isActive: boolean) => ReactNode;
  }[] = [
    {
      key: "home",
      label: "Home",
      icon: (active) => (
        <Ionicons
          name={active ? "home" : "home-outline"}
          size={20}
          color={active ? Colors.mainColour1 : "#6B7280"}
        />
      ),
    },
    {
      key: "plan",
      label: "Plan",
      icon: (active) => (
        <Ionicons
          name={active ? "calendar" : "calendar-outline"}
          size={20}
          color={active ? Colors.mainColour1 : "#6B7280"}
        />
      ),
    },
    {
      key: "today",
      label: "Today's Session",
      isCenter: true,
      icon: (active) => (
        <Ionicons
          name={active ? "today" : "today-outline"}
          size={20}
          color={Colors.white}
        />
      ),
    },
    {
      key: "profile",
      label: "Profile",
      icon: (active) => (
        <Ionicons
          name={active ? "person-circle" : "person-circle-outline"}
          size={20}
          color={active ? Colors.mainColour1 : "#6B7280"}
        />
      ),
    },
    {
      key: "more",
      label: "More",
      icon: (active) => (
        <Ionicons
          name={active ? "grid" : "grid-outline"}
          size={20}
          color={active ? Colors.mainColour1 : "#6B7280"}
        />
      ),
    },
  ];

  return (
    <View style={[styles.container, { paddingBottom: Math.max(insets.bottom, 8) }]}>
      {tabs.map((tab) => {
        const isActive = activeTab === tab.key;
        return (
          <Pressable
            key={tab.key}
            style={[styles.tabItem, tab.isCenter && styles.centerTabItem]}
            onPress={() => onSelectTab(tab.key)}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
          >
            {tab.isCenter ? (
              <View style={[styles.centerIconWrap, isActive && styles.centerIconWrapActive]}>
                {tab.icon(isActive)}
              </View>
            ) : (
              tab.icon(isActive)
            )}
            <AppText
              numberOfLines={1}
              style={[
                styles.tabLabel,
                tab.isCenter && styles.centerTabLabel,
                { color: isActive ? Colors.mainColour1 : tab.isCenter ? Colors.mainColour1 : "#6B7280" },
                isActive && styles.activeTabLabel,
              ]}
            >
              {tab.label}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-around",
    backgroundColor: Colors.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    paddingVertical: 6,
    borderTopWidth: 1,
    borderColor: "#F3F4F6",
    ...Shadows.raised,
  },
  tabItem: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 2,
    flex: 1,
  },
  centerTabItem: {
    marginTop: -8,
  },
  centerIconWrap: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: 2,
    shadowColor: Colors.mainColour1,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.35,
    shadowRadius: 5,
    elevation: 4,
  },
  centerIconWrapActive: {
    backgroundColor: "#004ECC",
    transform: [{ scale: 1.05 }],
  },
  tabLabel: {
    fontSize: 9.5,
    marginTop: 2,
    fontWeight: "500",
  },
  centerTabLabel: {
    fontSize: 8.5,
    fontWeight: "700",
  },
  activeTabLabel: {
    fontWeight: "700",
  },
});

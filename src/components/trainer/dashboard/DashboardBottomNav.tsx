import { ReactNode } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import AppText from "@/components/ui/AppText";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

export type DashboardTab = "home" | "plan" | "profile" | "more";

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
    icon: (isActive: boolean) => ReactNode;
  }[] = [
    {
      key: "home",
      label: "Home",
      icon: (active) => (
        <Ionicons
          name={active ? "home" : "home-outline"}
          size={21}
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
          size={21}
          color={active ? Colors.mainColour1 : "#6B7280"}
        />
      ),
    },
    {
      key: "profile",
      label: "Profile",
      icon: (active) => (
        <Ionicons
          name={active ? "person-circle" : "person-circle-outline"}
          size={21}
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
          size={21}
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
            style={styles.tabItem}
            onPress={() => onSelectTab(tab.key)}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
          >
            {tab.icon(isActive)}
            <AppText
              style={[
                styles.tabLabel,
                { color: isActive ? Colors.mainColour1 : "#6B7280" },
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
    paddingVertical: 8,
    borderTopWidth: 1,
    borderColor: "#F3F4F6",
    ...Shadows.raised,
  },
  tabItem: {
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 2,
    minWidth: 56,
  },
  tabLabel: {
    fontSize: 10,
    marginTop: 3,
    fontWeight: "500",
  },
  activeTabLabel: {
    fontWeight: "700",
  },
});

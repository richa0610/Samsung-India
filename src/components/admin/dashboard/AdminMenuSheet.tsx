import { Ionicons } from "@expo/vector-icons";
import { ReactNode, useEffect, useMemo, useState } from "react";
import { Animated, Easing, Modal, Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";

export type AdminMenuSheetItem = {
  key: string;
  label: string;
  icon: keyof typeof Ionicons.glyphMap;
  badge?: number;
};

type AdminMenuSheetProps = {
  visible: boolean;
  onClose: () => void;
  items: AdminMenuSheetItem[];
  onSelect: (key: string) => void;
  /** A copy of the bottom nav, drawn under the tiles so the sheet sits directly above the menu bar. */
  footer?: ReactNode;
};

/** Bottom-sheet icon grid opened by the admin menu's Training / Attendance tabs -
 *  same look as the trainer's More menu, sliding up from the bottom. */
const SLIDE_MS = 260;

export default function AdminMenuSheet({ visible, onClose, items, onSelect, footer }: AdminMenuSheetProps) {
  // Kept mounted through the closing slide so the sheet animates out too.
  const [mounted, setMounted] = useState(visible);
  const [sheetHeight, setSheetHeight] = useState(420);
  const progress = useMemo(() => new Animated.Value(0), []);

  if (visible && !mounted) setMounted(true);

  useEffect(() => {
    if (visible) {
      Animated.timing(progress, {
        toValue: 1,
        duration: SLIDE_MS,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }).start();
    } else if (mounted) {
      Animated.timing(progress, {
        toValue: 0,
        duration: SLIDE_MS,
        easing: Easing.in(Easing.cubic),
        useNativeDriver: true,
      }).start(({ finished }) => {
        if (finished) setMounted(false);
      });
    }
  }, [visible, mounted, progress]);

  if (!mounted) return null;

  const translateY = progress.interpolate({ inputRange: [0, 1], outputRange: [sheetHeight, 0] });

  return (
    <Modal visible transparent animationType="none" statusBarTranslucent onRequestClose={onClose}>
      <View style={styles.root}>
        <Animated.View style={[styles.backdrop, { opacity: progress }]}>
          <Pressable style={StyleSheet.absoluteFill} onPress={onClose} accessibilityLabel="Close menu" />
        </Animated.View>
        <Animated.View
          collapsable={false}
          style={[styles.sheet, { transform: [{ translateY }] }]}
          onLayout={(event) => setSheetHeight(event.nativeEvent.layout.height)}
        >
      <View style={styles.grid}>
        {items.map((item) => (
          <Pressable
            key={item.key}
            style={styles.item}
            onPress={() => onSelect(item.key)}
            hitSlop={4}
            accessibilityRole="button"
            accessibilityLabel={item.label}
          >
            <View style={styles.iconWrap}>
              <Ionicons name={item.icon} size={22} color={Colors.mainColour1} />
              {!!item.badge && item.badge > 0 && (
                <View style={styles.badge}>
                  <AppText style={styles.badgeText} color={Colors.white} weight={FontWeight.bold}>
                    {item.badge > 99 ? "99+" : item.badge}
                  </AppText>
                </View>
              )}
            </View>
            <AppText style={styles.label} weight={FontWeight.medium}>
              {item.label}
            </AppText>
          </Pressable>
        ))}
      </View>
          {footer}
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, justifyContent: "flex-end" },
  backdrop: { ...StyleSheet.absoluteFill, backgroundColor: "rgba(0,0,0,0.4)" },
  sheet: {
    width: "100%",
    backgroundColor: Colors.white,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    overflow: "hidden",
  },
  grid: { flexDirection: "row", flexWrap: "wrap", paddingHorizontal: 12, paddingTop: 8, paddingBottom: 20 },
  item: { width: "25%", alignItems: "center", gap: 6, paddingVertical: 12 },
  iconWrap: {
    width: 52,
    height: 52,
    borderRadius: Radius.lg,
    backgroundColor: "#EAF2FF",
    alignItems: "center",
    justifyContent: "center",
  },
  label: { fontSize: Fonts.caption, textAlign: "center", lineHeight: 14 },
  badge: {
    position: "absolute",
    top: -5,
    right: -5,
    minWidth: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: "#DC2626",
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 4,
  },
  badgeText: { fontSize: 10 },
});

import { ReactNode } from "react";
import { StyleProp, StyleSheet, View, ViewStyle } from "react-native";
import { StatusBar } from "expo-status-bar";

type Props = {
  backgroundColor: string;
  children: ReactNode;
  style?: StyleProp<ViewStyle>;
  statusBarStyle?: "light" | "dark";
};

/** Colored, rounded-bottom header shell - the mainColour1 banner on the
 * trainer dashboard, reused wherever else a screen wants that same
 * full-bleed colored header. */
export default function ScreenBanner({ backgroundColor, children, style, statusBarStyle = "dark" }: Props) {
  return (
    <>
      <StatusBar style={statusBarStyle} />
      <View style={[styles.banner, { backgroundColor }, style]}>{children}</View>
    </>
  );
}

const styles = StyleSheet.create({
  banner: {
    paddingHorizontal: 20,
    paddingTop: 12,
    paddingBottom: 24,
    },
});

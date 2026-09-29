import { StyleSheet } from "react-native";
import { Colors } from "@/theme/colors";

export const styles = StyleSheet.create({
  container: {
    flex: 1,
  },

  overlay: {
    ...StyleSheet.absoluteFill,
  },

  keyboard: {
    flex: 1,
  },

  alignBottom: {
    justifyContent: "flex-end",
  },

  alignTop: {
    justifyContent: "flex-start",
  },

  alignLeft: {
    flexDirection: "row",
    justifyContent: "flex-start",
  },

  alignRight: {
    flexDirection: "row",
    justifyContent: "flex-end",
  },

  alignCenter: {
    justifyContent: "center",
    alignItems: "center",
  },

  content: {
    backgroundColor: Colors.white,
  },

  bottom: {
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: "90%",
  },

  top: {
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
    maxHeight: "100%",
  },

  left: {
    alignSelf: "stretch",
    width: "82%",
  },

  right: {
    alignSelf: "stretch",
    width: "82%",
  },

  center: {
    alignSelf: "center",
    justifyContent: "center",
    borderRadius: 20,
  },
});
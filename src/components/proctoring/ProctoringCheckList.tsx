import React from "react";
import { StyleSheet, View } from "react-native";

import ProctoringCheckItem, {
  ProctoringCheckItemData,
} from "./ProctoringCheckItem";

export const DEFAULT_PROCTORING_CHECKS: ProctoringCheckItemData[] = [
  {
    id: "camera",
    icon: "camera-outline",
    title: "Camera Access",
    description: "We will access your camera to monitor your activity.",
    checked: true,
  },
  {
    id: "face",
    icon: "scan-outline",
    title: "Face Detection",
    description: "Your face will be detected throughout the test.",
    checked: true,
  },
  {
    id: "multiple_person",
    icon: "people-outline",
    title: "Multiple Person Detection",
    description: "We will detect if more than one person is present.",
    checked: true,
  },
  {
    id: "tab_switching",
    icon: "phone-portrait-outline",
    title: "Tab Switching Detection",
    description: "Avoid switching apps or browser tabs during the test.",
    checked: true,
  },
];

export type ProctoringCheckListProps = {
  checks?: ProctoringCheckItemData[];
};

export default function ProctoringCheckList({
  checks = DEFAULT_PROCTORING_CHECKS,
}: ProctoringCheckListProps) {
  return (
    <View style={styles.container}>
      {checks.map((item, index) => (
        <React.Fragment key={item.id}>
          <ProctoringCheckItem item={item} />
          {index < checks.length - 1 && <View style={styles.divider} />}
        </React.Fragment>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#FFFFFF",
    borderRadius: 16,
    borderWidth: 1,
    borderColor: "#F3F4F6",
    paddingHorizontal: 14,
    paddingVertical: 4,
  },
  divider: {
    height: 1,
    backgroundColor: "#F3F4F6",
  },
});

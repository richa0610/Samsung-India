import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import { AssessmentSuiteOut } from "@/api/training";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import DashboardSectionCard from "./DashboardSectionCard";
import SuiteRow from "./SuiteRow";

type AssessmentSuitesCardProps = {
  suites: AssessmentSuiteOut[];
  loading: boolean;
  onAddSuite: () => void;
  onSelectSuite: (suiteUid: string) => void;
};

export default function AssessmentSuitesCard({ suites, loading, onAddSuite, onSelectSuite }: AssessmentSuitesCardProps) {
  return (
    <DashboardSectionCard
      icon="document-text-outline"
      title="Assessment Suites"
      badge={
        <Pressable style={styles.addSuiteButton} onPress={onAddSuite}>
          <Ionicons name="add" size={16} color={Colors.white} />
          <AppText style={styles.addSuiteButtonText} color={Colors.white} weight={FontWeight.semiBold}>
            Add Suite
          </AppText>
        </Pressable>
      }
      loading={loading}
      isEmpty={suites.length === 0}
      emptyIcon="document-outline"
      emptyText="No assessment suites yet."
    >
      <View style={styles.suiteList}>
        {suites.map((suite) => (
          <SuiteRow
            key={suite.assessmentSuiteUid}
            suite={suite}
            onPress={() => onSelectSuite(suite.assessmentSuiteUid)}
          />
        ))}
      </View>
    </DashboardSectionCard>
  );
}

const styles = StyleSheet.create({
  addSuiteButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    backgroundColor: Colors.mainColour1,
    borderRadius: Radius.lg,
    paddingHorizontal: 10,
    paddingVertical: 6,
  },
  addSuiteButtonText: { fontSize: Fonts.overline },
  suiteList: { marginTop: 10, gap: 8 },
});

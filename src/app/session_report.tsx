import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useState } from "react";
import { ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { fetchSessionReport, SessionReport } from "@/api/training";
import { DataTable } from "@/components/ui/DataTable";
import {
  SessionReportHeader,
  SessionSummaryCard,
  useSessionReportColumns,
} from "@/components/session_report";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";

export default function SessionReportScreen() {
  const router = useRouter();
  const params = useLocalSearchParams<{ conferenceUid?: string }>();
  const conferenceUid = params.conferenceUid || "";
  const { adminToken } = useAuth();

  const [report, setReport] = useState<SessionReport | null>(null);
  const columns = useSessionReportColumns();

  const loadData = useCallback(async () => {
    if (!adminToken || !conferenceUid) return;
    try {
      setReport(await fetchSessionReport(adminToken, conferenceUid));
    } catch {
      setReport(null);
    }
  }, [adminToken, conferenceUid]);

  useFocusEffect(
    useCallback(() => {
      loadData();
    }, [loadData]),
  );

  const summary = {
    conferenceId: report?.summary.conferenceId || conferenceUid || "--",
    sessionName: report?.summary.sessionName || "--",
    date: report?.summary.date || "--",
    state: report?.summary.state || "--",
    schedule: report?.summary.schedule || "--",
    duration: report?.summary.duration || "--",
    venueLink: report?.summary.venueLink || "--",
  };

  return (
    <SafeAreaView style={styles.container} edges={["bottom"]}>
      <SessionReportHeader onBack={() => router.back()} />

      <ScrollView style={styles.scroll} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SessionSummaryCard summary={summary} />

        <View style={styles.tableWrap}>
          <DataTable
            title="Quiz Participant Details"
            columns={columns}
            data={report?.liveQuiz ?? []}
            keyExtractor={(row, index) => `quiz-${row.userId}-${index}`}
            exportFileName="quiz-participant-details"
            toolbarVariant="download"
            headerBackgroundColor={Colors.mainColour1}
            headerTextColor={Colors.white}
          />
        </View>

        <View style={styles.tableWrap}>
          <DataTable
            title="Test Participant Details"
            columns={columns}
            data={report?.standardTest ?? []}
            keyExtractor={(row, index) => `test-${row.userId}-${index}`}
            exportFileName="test-participant-details"
            toolbarVariant="download"
            headerBackgroundColor={Colors.mainColour1}
            headerTextColor={Colors.white}
          />
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#F3F7FA" },
  scroll: { marginTop: -50, zIndex: 1, elevation: 1 },
  content: { flexGrow: 1, paddingBottom: 24 },
  tableWrap: { marginHorizontal: 14, marginTop: 16 },
});

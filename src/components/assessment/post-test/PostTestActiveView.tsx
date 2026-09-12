import { ScrollView, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import SecurityLockedView from "@/components/assessment/SecurityLockedView";
import ProctoringSoftWarning from "@/components/proctoring/ProctoringSoftWarning";
import SecurityViolationModal from "@/components/proctoring/SecurityViolationModal";
import { MAX_PROCTORING_WARNINGS } from "@/components/proctoring/violations";
import { usePostTest } from "@/hooks/usePostTest";
import { Colors } from "@/theme/colors";
import PostTestHeader from "./PostTestHeader";
import PostTestScrollContent from "./PostTestScrollContent";

type PostTestActiveViewProps = {
  postTest: ReturnType<typeof usePostTest>;
};

export default function PostTestActiveView({ postTest }: PostTestActiveViewProps) {
  const {
    violationModalVisible,
    testStatus,
    violationCount,
    currentViolation,
    handleCloseViolationModal,
    softWarningType,
    lockedViolationType,
    handleSecurityLockedClose,
    remainingMinutes,
    remainingSecondsPart,
    questionIndex,
    questions,
  } = postTest;

  return (
    <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
      {/* Security Violation Modal (Strikes 1 & 2 only) */}
      <SecurityViolationModal
        visible={violationModalVisible && testStatus === "active" && violationCount < MAX_PROCTORING_WARNINGS}
        violationType={currentViolation}
        strikesRemaining={Math.max(MAX_PROCTORING_WARNINGS - violationCount, 0)}
        maxStrikes={MAX_PROCTORING_WARNINGS}
        onClose={handleCloseViolationModal}
        isTerminal={false}
      />

      {/* Soft (non-strike) warning — earlier heads-up before a strike lands */}
      <ProctoringSoftWarning visible={!!softWarningType && testStatus === "active"} violationType={softWarningType} />

      {/* Security Locked Overlay (Post test auto-terminated / locked state) */}
      {testStatus === "security-locked" && (
        <SecurityLockedView
          violationType={lockedViolationType || currentViolation}
          onClose={handleSecurityLockedClose}
        />
      )}

      <PostTestHeader
        remainingMinutes={remainingMinutes}
        remainingSecondsPart={remainingSecondsPart}
        questionIndex={questionIndex}
        questionsLength={questions.length}
      />

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <PostTestScrollContent postTest={postTest} />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  scrollView: { flex: 1 },
  content: {
    flexGrow: 1,
    padding: 13,
    gap: 11,
    paddingBottom: 16,
  },
});

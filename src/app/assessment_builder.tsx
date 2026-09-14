import { useLocalSearchParams, useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";
import { ActivityIndicator, Pressable, ScrollView, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";

import {
  AddQuestionModal,
  BuilderHeader,
  QuestionsList,
  SuiteFormCard,
} from "@/components/admin/assessment-builder";
import { useAssessmentBuilder } from "@/hooks/useAssessmentBuilder";
import { Colors } from "@/theme/colors";
import { Shadows } from "@/theme/shadows";

export default function AssessmentBuilderScreen() {
  const router = useRouter();
  const { suiteUid: suiteUidParam } = useLocalSearchParams<{ suiteUid?: string }>();

  const {
    adminToken,
    suite,
    loading,
    error,
    title,
    setTitle,
    description,
    setDescription,
    category,
    setCategory,
    testTime,
    setTestTime,
    type,
    setType,
    creating,
    addVisible,
    setAddVisible,
    handleCreateSuite,
    handleDeleteQuestion,
    handleQuestionAdded,
  } = useAssessmentBuilder(suiteUidParam);

  if (loading) {
    return (
      <SafeAreaView style={styles.loadingContainer}>
        <ActivityIndicator color={Colors.mainColour1} size="large" />
      </SafeAreaView>
    );
  }

  return (
    <>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
        <BuilderHeader onBack={() => router.back()} />

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <SuiteFormCard
            suite={suite}
            title={title}
            setTitle={setTitle}
            description={description}
            setDescription={setDescription}
            category={category}
            setCategory={setCategory}
            testTime={testTime}
            setTestTime={setTestTime}
            type={type}
            setType={setType}
            error={error}
            creating={creating}
            onCreateSuite={handleCreateSuite}
          />

          {suite && (
            <QuestionsList questions={suite.questions} onDeleteQuestion={handleDeleteQuestion} />
          )}
        </ScrollView>

        {suite && (
          <Pressable style={styles.fab} onPress={() => setAddVisible(true)}>
            <Ionicons name="add" size={26} color={Colors.white} />
          </Pressable>
        )}
      </SafeAreaView>

      {suite && (
        <AddQuestionModal
          visible={addVisible}
          onClose={() => setAddVisible(false)}
          onAdded={handleQuestionAdded}
          adminToken={adminToken}
          suiteUid={suite.assessmentSuiteUid}
        />
      )}
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  content: { flexGrow: 1, padding: 16, gap: 14, paddingBottom: 80 },
  loadingContainer: { flex: 1, alignItems: "center", justifyContent: "center" },
  fab: {
    position: "absolute",
    right: 20,
    bottom: 24,
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.mainColour1,
    alignItems: "center",
    justifyContent: "center",
    ...Shadows.raised,
  },
});

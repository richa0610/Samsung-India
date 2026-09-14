import { StyleSheet, ScrollView } from "react-native";

import { AssessmentSuiteDetail } from "@/api/training";
import AppButton from "@/components/ui/AppButton";
import AppInput from "@/components/ui/AppInput";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { useAddQuestionModal } from "@/hooks/useAddQuestionModal";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import QuestionMetaFields from "./QuestionMetaFields";
import QuestionOptionsEditor from "./QuestionOptionsEditor";

type AddQuestionModalProps = {
  visible: boolean;
  onClose: () => void;
  onAdded: (updated: AssessmentSuiteDetail) => void;
  adminToken: string | null;
  suiteUid: string;
};

export default function AddQuestionModal({ visible, onClose, onAdded, adminToken, suiteUid }: AddQuestionModalProps) {
  const {
    question,
    setQuestion,
    questionType,
    setQuestionType,
    points,
    setPoints,
    timerSeconds,
    setTimerSeconds,
    options,
    correctAnswer,
    setCorrectAnswer,
    saving,
    error,
    reset,
    handleAddOption,
    handleUpdateOption,
    handleRemoveOption,
    handleSave,
  } = useAddQuestionModal({ adminToken, suiteUid, onAdded });

  return (
    <AppModal
      visible={visible}
      onClose={() => {
        reset();
        onClose();
      }}
      position="bottom"
      title="Add Question"
      showCloseButton
      contentStyle={styles.sheet}
    >
      <ScrollView contentContainerStyle={styles.sheetContent} keyboardShouldPersistTaps="handled">
        <AppInput placeholder="Question" value={question} onChangeText={setQuestion} />

        <QuestionMetaFields
          questionType={questionType}
          setQuestionType={setQuestionType}
          points={points}
          setPoints={setPoints}
          timerSeconds={timerSeconds}
          setTimerSeconds={setTimerSeconds}
        />

        <QuestionOptionsEditor
          options={options}
          correctAnswer={correctAnswer}
          onSelectCorrect={setCorrectAnswer}
          onUpdateOption={handleUpdateOption}
          onRemoveOption={handleRemoveOption}
          onAddOption={handleAddOption}
        />

        {error && <AppText style={styles.errorText}>{error}</AppText>}

        <AppButton title="Save Question" onPress={handleSave} loading={saving} buttonStyle={styles.saveButton} />
      </ScrollView>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: {
    maxHeight: "85%",
    borderTopLeftRadius: Radius.xxxl,
    borderTopRightRadius: Radius.xxxl,
  },
  sheetContent: { padding: 16, gap: 10 },
  errorText: {
    color: Colors.danger,
    fontSize: Fonts.bodySm,
    textAlign: "center",
  },
  saveButton: { marginTop: 16 },
});

import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import { QuestionOption } from "@/api/training";
import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";

type QuestionOptionsEditorProps = {
  options: QuestionOption[];
  correctAnswer: string;
  onSelectCorrect: (id: string) => void;
  onUpdateOption: (id: string, text: string) => void;
  onRemoveOption: (id: string) => void;
  onAddOption: () => void;
};

export default function QuestionOptionsEditor({
  options,
  correctAnswer,
  onSelectCorrect,
  onUpdateOption,
  onRemoveOption,
  onAddOption,
}: QuestionOptionsEditorProps) {
  return (
    <>
      <AppText style={[styles.fieldLabel, styles.optionsLabel]} weight={FontWeight.medium}>
        Options (select the correct answer)
      </AppText>
      {options.map((opt, idx) => (
        <View key={opt.id} style={styles.optionInputRow}>
          <Pressable onPress={() => onSelectCorrect(opt.id)} hitSlop={8} style={styles.radioHit}>
            <Ionicons
              name={opt.id === correctAnswer ? "radio-button-on" : "radio-button-off"}
              size={20}
              color={opt.id === correctAnswer ? Colors.mainColour1 : Colors.gray400}
            />
          </Pressable>
          <View style={styles.optionInputContainer}>
            <AppInput
              placeholder={`Option ${idx + 1}`}
              value={opt.text}
              onChangeText={(text) => onUpdateOption(opt.id, text)}
            />
          </View>
          {options.length > 2 && (
            <Pressable onPress={() => onRemoveOption(opt.id)} hitSlop={8}>
              <Ionicons name="close-circle-outline" size={20} color={Colors.gray400} />
            </Pressable>
          )}
        </View>
      ))}

      <Pressable style={styles.addOptionButton} onPress={onAddOption}>
        <Ionicons name="add" size={16} color={Colors.mainColour1} />
        <AppText color={Colors.mainColour1} weight={FontWeight.medium} style={styles.addOptionText}>
          Add Option
        </AppText>
      </Pressable>
    </>
  );
}

const styles = StyleSheet.create({
  fieldLabel: { fontSize: Fonts.caption, marginBottom: 4 },
  optionsLabel: { marginTop: 12 },
  optionInputRow: { flexDirection: "row", alignItems: "center", gap: 8 },
  radioHit: { padding: 2 },
  optionInputContainer: { flex: 1, marginBottom: 0 },
  addOptionButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 6,
  },
  addOptionText: { fontSize: Fonts.bodySm },
});

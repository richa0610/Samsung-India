import { Ionicons } from "@expo/vector-icons";
import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontSize, FontWeight, LineHeight } from "@/theme/typography";

type QuestionOptionsListProps = {
  options: { id: string; text: string }[];
  selectedOption: string | null;
  isActive: boolean;
  onSelect: (optionId: string) => void;
};

export default function QuestionOptionsList({ options, selectedOption, isActive, onSelect }: QuestionOptionsListProps) {
  return (
    <View style={styles.options}>
      {options.map((option) => {
        const checked = selectedOption === option.id;
        return (
          <Pressable
            key={option.id}
            style={[styles.option, checked && styles.optionSelected, !isActive && styles.optionDisabled]}
            onPress={() => onSelect(option.id)}
            disabled={!isActive}
          >
            <View style={[styles.checkbox, checked && styles.checkboxSelected]}>
              {checked && <Ionicons name="checkmark" size={13} color={Colors.white} />}
            </View>
            <AppText style={styles.optionText} weight={FontWeight.medium}>
              {option.text}
            </AppText>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  options: { gap: 8 },
  option: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 12,
    backgroundColor: "#FFFFFF",
    minHeight: 56,
    borderWidth: 1.5,
    borderColor: Colors.slate200,
    gap: 10,
  },
  optionSelected: {
    backgroundColor: "#F0F7FF",
    borderColor: "#006AFF",
  },
  optionDisabled: { opacity: 0.6 },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 5,
    borderWidth: 1.5,
    borderColor: "#CBD5E1",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#FFFFFF",
  },
  checkboxSelected: {
    backgroundColor: "#006AFF",
    borderColor: "#006AFF",
  },
  optionText: {
    fontSize: FontSize.label,
    lineHeight: LineHeight.label,
    color: "#000000",
    flex: 1,
  },
});

import React from "react";
import { StyleSheet, TextInput, View } from "react-native";

import { Colors } from "@/theme/colors";

export type SurveyTextInputProps = {
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  hasError?: boolean;
};

export default function SurveyTextInput({
  value,
  onChangeText,
  placeholder = "Type your response here...",
  hasError = false,
}: SurveyTextInputProps) {
  return (
    <View style={[styles.container, hasError && styles.containerError]}>
      <TextInput
        style={styles.input}
        placeholder={placeholder}
        placeholderTextColor={Colors.gray400}
        value={value}
        onChangeText={onChangeText}
        multiline
        numberOfLines={4}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    borderWidth: 1.2,
    borderColor: Colors.gray200,
    borderRadius: 12,
    backgroundColor: Colors.white,
    padding: 10,
    minHeight: 96,
  },
  containerError: {
    borderColor: Colors.danger,
    backgroundColor: Colors.dangerBgSoft,
  },
  input: {
    flex: 1,
    fontSize: 13.5,
    color: Colors.gray800,
    textAlignVertical: "top",
    lineHeight: 19,
    minHeight: 76,
  },
});

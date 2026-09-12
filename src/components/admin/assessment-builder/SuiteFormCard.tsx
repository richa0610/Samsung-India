import { StyleSheet, View } from "react-native";

import { AssessmentSuiteDetail } from "@/api/training";
import AppButton from "@/components/ui/AppButton";
import AppInput from "@/components/ui/AppInput";
import AppSelect from "@/components/ui/AppSelect";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";
import { Shadows } from "@/theme/shadows";
import { digitsOnly } from "@/utils/validation";
import { CATEGORY_OPTIONS, TYPE_OPTIONS } from "./constants";
import SuiteField from "./SuiteField";

type SuiteFormCardProps = {
  suite: AssessmentSuiteDetail | null;
  title: string;
  setTitle: (value: string) => void;
  description: string;
  setDescription: (value: string) => void;
  category: string;
  setCategory: (value: string) => void;
  testTime: string;
  setTestTime: (value: string) => void;
  type: string;
  setType: (value: string) => void;
  error: string | null;
  creating: boolean;
  onCreateSuite: () => void;
};

export default function SuiteFormCard({
  suite,
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
  error,
  creating,
  onCreateSuite,
}: SuiteFormCardProps) {
  return (
    <View style={styles.card}>
      <AppInput
        placeholder="Untitled Assessment"
        value={suite?.title ?? title}
        onChangeText={setTitle}
        editable={!suite}
      />
      <AppInput
        placeholder="Form description"
        value={suite?.description ?? description}
        onChangeText={setDescription}
        editable={!suite}
      />

      <View style={styles.row}>
        <SuiteField label="Category *" readonlyValue={suite?.category}>
          <AppSelect
            selectedValue={category}
            onValueChange={setCategory}
            items={[
              { label: "Select Category", value: "" },
              ...CATEGORY_OPTIONS.map((c) => ({ label: c, value: c })),
            ]}
          />
        </SuiteField>
        <SuiteField label="Time (min) *" readonlyValue={suite ? (suite.testTime ?? "--") : undefined}>
          <AppInput
            placeholder="30"
            keyboardType="number-pad"
            maxLength={3}
            value={testTime}
            onChangeText={(v) => setTestTime(digitsOnly(v))}
          />
        </SuiteField>
        <SuiteField label="Type" readonlyValue={suite?.type}>
          <AppSelect
            selectedValue={type}
            onValueChange={setType}
            items={TYPE_OPTIONS.map((t) => ({ label: t, value: t }))}
          />
        </SuiteField>
      </View>

      {error && <AppText style={styles.errorText}>{error}</AppText>}

      {!suite && (
        <AppButton
          title="Create & Continue"
          onPress={onCreateSuite}
          loading={creating}
          buttonStyle={styles.createButton}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.white,
    borderRadius: Radius.xxl,
    padding: 16,
    gap: 10,
    ...Shadows.card,
  },
  row: { flexDirection: "row", gap: 10 },
  createButton: { marginTop: 8 },
  errorText: {
    color: Colors.danger,
    fontSize: Fonts.bodySm,
    textAlign: "center",
  },
});

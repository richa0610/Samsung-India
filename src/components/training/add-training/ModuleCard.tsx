import { Ionicons } from "@expo/vector-icons";
import { Pressable, View } from "react-native";

import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { digitsOnly } from "@/utils/validation";
import { MODULE_COLORS, MODULE_ICONS, MODULE_LABELS, ModuleKey, UNLOCK_CONDITIONS } from "./constants";
import { DateTimeField } from "./DateTimeField";
import { flowCardStyles as s } from "./flowCardStyles";
import { AddTrainingForm } from "./useAddTrainingForm";

export function ModuleCard({ moduleKey: key, form }: { moduleKey: ModuleKey; form: AddTrainingForm }) {
  const moduleState = form.modules[key];
  const selectedSuite = form.assessmentSuites.find((suite) => suite.assessmentSuiteUid === moduleState.assessmentSuiteUid);

  return (
    <View style={s.card}>
      <View style={s.header}>
        <Ionicons name={MODULE_ICONS[key]} size={16} color={MODULE_COLORS[key]} />
        <AppText style={s.headerTitle} weight={FontWeight.semiBold}>{MODULE_LABELS[key].toUpperCase()}</AppText>
      </View>
      <View style={s.headerDivider} />

      <SearchableSelect
        label="Category"
        compact
        placeholder="Select Category..."
        value={moduleState.category ?? ""}
        options={form.categoryOptions}
        onSelect={(option) =>
          form.updateModule(key, { category: option.value, assessmentSuiteUid: undefined, questionCount: "" })
        }
      />
      <View style={s.row}>
        <View style={s.half}>
          <SearchableSelect
            label="Select Question Set"
            compact
            placeholder={moduleState.category ? "Select Test" : "Select Category First"}
            value={moduleState.assessmentSuiteUid ?? ""}
            options={form.questionSetOptionsFor(moduleState.category)}
            onSelect={(option) => {
              const suite = form.assessmentSuites.find((item) => item.assessmentSuiteUid === option.value);
              form.updateModule(key, {
                assessmentSuiteUid: option.value,
                questionCount: suite ? String(suite.noOfQuestion) : "",
              });
            }}
            disabled={!moduleState.category}
          />
        </View>
        <View style={s.half}>
          <View style={s.questionsLabelRow}>
            <AppText style={s.fieldLabel} weight={FontWeight.medium}>Questions</AppText>
            {moduleState.assessmentSuiteUid && (
              <View style={s.maxBadge}>
                <AppText style={s.maxBadgeText} color={Colors.white}>Max: {selectedSuite?.noOfQuestion ?? 0}</AppText>
              </View>
            )}
          </View>
          <AppInput
            compact
            placeholder="Number of questions"
            keyboardType="number-pad"
            maxLength={4}
            value={moduleState.questionCount}
            onChangeText={(text) => form.updateModule(key, { questionCount: digitsOnly(text) })}
            editable={!!moduleState.assessmentSuiteUid}
          />
        </View>
      </View>
      <View style={s.row}>
        <View style={s.half}>
          <DateTimeField
            compact
            label="Start Time"
            value={moduleState.startTime ?? ""}
            mode="time"
            onChange={(v) => form.updateModule(key, { startTime: v })}
            plain
          />
        </View>
        <View style={s.half}>
          <DateTimeField
            compact
            label="End Time"
            value={moduleState.endTime ?? ""}
            mode="time"
            onChange={(v) => form.updateModule(key, { endTime: v })}
            plain
          />
        </View>
      </View>
      <Pressable style={s.checkboxRow} onPress={() => form.updateModule(key, { checkIn: !moduleState.checkIn })}>
        <View style={[s.checkbox, moduleState.checkIn && s.checkboxChecked]}>
          {moduleState.checkIn && <Ionicons name="checkmark" size={12} color={Colors.white} />}
        </View>
        <AppText style={s.checkboxLabel}>Check-in</AppText>
      </Pressable>
      <AppText style={s.fieldLabel} weight={FontWeight.medium}>Unlock Condition</AppText>
      <SearchableSelect
        compact
        value={moduleState.unlockCondition ?? "Automatic"}
        options={UNLOCK_CONDITIONS.map((u) => ({ label: u, value: u }))}
        onSelect={(option) => form.updateModule(key, { unlockCondition: option.value })}
      />
    </View>
  );
}

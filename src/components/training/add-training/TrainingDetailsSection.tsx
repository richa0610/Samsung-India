import { useMemo } from "react";
import { Pressable, StyleSheet, Switch } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import AppText from "@/components/ui/AppText";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Spacing } from "@/theme/spacing";
import { digitsOnly } from "@/utils/validation";
import { DateTimeField } from "./DateTimeField";
import { SectionTitle } from "./SectionTitle";
import { AddTrainingForm } from "./useAddTrainingForm";

export function TrainingDetailsSection({ form }: { form: AddTrainingForm }) {
  const today = useMemo(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  }, []);
  // End Date can't be before whichever training date the trainer already
  // picked - the training date field itself already blocks past dates.
  const parsedTrainingDate = form.conferenceDate ? new Date(form.conferenceDate) : null;
  const endDateMinimum = parsedTrainingDate && parsedTrainingDate > today ? parsedTrainingDate : today;

  return (
    <AppCard style={styles.card}>
      <SectionTitle index={3} title="Training Details" icon="people-outline" />
      <Pressable style={styles.toggleRow} onPress={() => form.toggleResidential(!form.isResidential)}>
        <AppText style={styles.toggleLabel}>Is this an Residential Program ?</AppText>
        <Switch value={form.isResidential} onValueChange={form.toggleResidential} trackColor={{ true: Colors.mainColour1 }} />
      </Pressable>

      <DateTimeField
        compact
        label="Training Date *"
        value={form.conferenceDate}
        mode="date"
        onChange={form.setConferenceDate}
        minimumDate={today}
      />
      {form.isResidential && (
        <DateTimeField
          compact
          label="End Date *"
          value={form.trainingEndDate}
          mode="date"
          onChange={form.setTrainingEndDate}
          minimumDate={endDateMinimum}
        />
      )}
      <DateTimeField compact label="Start Time *" value={form.conferenceTime} mode="time" onChange={form.setConferenceTime} />
      <SearchableSelect
        label="Training Hub"
        compact
        placeholder="Select Hub"
        icon="business-outline"
        value={form.trainingHub}
        options={form.trainingHubOptions}
        onSelect={(option) => form.setTrainingHub(option.value)}
      />
      <SearchableSelect
        label="Audience"
        compact
        placeholder="Select Audience"
        icon="school-outline"
        value={form.audience}
        options={form.audienceOptions}
        onSelect={(option) => form.setAudience(option.value)}
      />
      <SearchableSelect
        label="Session Type"
        compact
        placeholder="Select Session Type"
        icon="person-outline"
        value={form.sessionType}
        options={form.sessionTypeOptions}
        onSelect={(option) => form.setSessionType(option.value)}
      />
      <SearchableSelect
        label="Training Type"
        compact
        placeholder="Select Training Type"
        icon="wifi-outline"
        value={form.trainingType}
        options={form.trainingTypeOptions}
        onSelect={(option) => form.setTrainingType(option.value)}
      />
      <AppInput
        compact
        label="Batch Size"
        placeholder="Enter Batch Size"
        icon="people-outline"
        keyboardType="number-pad"
        maxLength={6}
        value={form.batchSize}
        onChangeText={(v) => form.setBatchSize(digitsOnly(v))}
      />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
  toggleRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: Spacing.lg,
  },
  toggleLabel: { fontSize: Fonts.body, color: Colors.gray600, flex: 1, marginRight: 12 },
});

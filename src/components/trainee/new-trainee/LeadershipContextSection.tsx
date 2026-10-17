import { StyleSheet } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { SectionTitle } from "@/components/training/add-training/SectionTitle";
import { SUPERVISOR_DESIGNATION_OPTIONS } from "./constants";
import { NewTraineeForm } from "./useNewTraineeForm";

export function LeadershipContextSection({ form }: { form: NewTraineeForm }) {
  const trainerPlaceholder = form.company ? "Select Trainer" : "Select Company First";
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={2} title="Leadership Context" icon="people-outline" />
      <SearchableSelect
        label="Trainer ID"
        required
        placeholder={trainerPlaceholder}
        icon="briefcase-outline"
        value={form.trainerId}
        options={form.trainerOptions}
        disabled={!form.company}
        onSelect={(option) => {
          form.setTrainerId(option.value);
          form.setTrainerName(option.label.split(" - ")[1] ?? "");
        }}
      />
      <AppInput label="Trainer Name" placeholder="Auto-fetched name" value={form.trainerName} editable={false} />
      <SearchableSelect
        label="Supervisor ID"
        required
        placeholder={trainerPlaceholder}
        icon="briefcase-outline"
        value={form.supervisorId}
        options={form.trainerOptions}
        disabled={!form.company}
        onSelect={(option) => {
          form.setSupervisorId(option.value);
          form.setSupervisorName(option.label.split(" - ")[1] ?? "");
        }}
      />
      <AppInput label="Supervisor Name" placeholder="Auto-fetched name" value={form.supervisorName} editable={false} />
      <SearchableSelect
        label="Supervisor Designation"
        placeholder="e.g. Area Manager"
        icon="briefcase-outline"
        value={form.supervisorDesignation}
        options={SUPERVISOR_DESIGNATION_OPTIONS}
        onSelect={(option) => form.setSupervisorDesignation(option.value)}
      />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
});

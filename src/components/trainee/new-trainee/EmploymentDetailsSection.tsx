import { StyleSheet } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { DateTimeField } from "@/components/training/add-training/DateTimeField";
import { SectionTitle } from "@/components/training/add-training/SectionTitle";
import { digitsOnly } from "@/utils/validation";
import { JOB_STATUS_OPTIONS } from "./constants";
import { NewTraineeForm } from "./useNewTraineeForm";

export function EmploymentDetailsSection({ form }: { form: NewTraineeForm }) {
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={5} title="Employment Details" icon="briefcase-outline" />
      <DateTimeField label="Joined On" mode="date" value={form.joinedOn} onChange={form.setJoinedOn} />
      <SearchableSelect
        label="Job Status"
        placeholder="Select Status"
        icon="person-outline"
        value={form.jobStatus}
        options={JOB_STATUS_OPTIONS}
        onSelect={(option) => form.setJobStatus(option.value)}
      />
      <AppInput
        label="Job City"
        placeholder="Current Work City"
        icon="business-outline"
        autoCapitalize="words"
        value={form.jobCity}
        onChangeText={form.setJobCity}
      />
      <AppInput
        label="Job Pincode"
        placeholder="Current Work Pincode"
        icon="location-outline"
        keyboardType="number-pad"
        maxLength={6}
        value={form.jobPincode}
        onChangeText={(v) => form.setJobPincode(digitsOnly(v))}
      />
      <DateTimeField
        label="Resigned On"
        mode="date"
        value={form.resignedOn}
        onChange={form.setResignedOn}
        disabled={form.jobStatus !== "Resigned"}
      />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
});

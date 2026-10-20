import { StyleSheet } from "react-native";

import CompanyField from "@/components/company/CompanyField";
import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { SectionTitle } from "@/components/training/add-training/SectionTitle";
import { REQUESTED_BY_OPTIONS } from "./constants";
import { NewTraineeForm } from "./useNewTraineeForm";

export function CorporateMappingSection({ form }: { form: NewTraineeForm }) {
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={1} title="Corporate Mapping" icon="globe-outline" />
      <SearchableSelect
        label="Zone"
        required
        placeholder="Select Zone"
        icon="location-outline"
        value={form.zone}
        options={form.zoneOptions}
        onSelect={(option) => {
          form.setZone(option.value);
          form.setRegion("");
        }}
      />
      <SearchableSelect
        label="Region"
        required
        placeholder={form.zone ? "Select Region" : "Select Zone First"}
        icon="globe-outline"
        value={form.region}
        options={form.regionOptions}
        onSelect={(option) => form.setRegion(option.value)}
        disabled={!form.zone}
      />
      <CompanyField value={form.company} />
      <SearchableSelect
        label="Requested By"
        required
        placeholder="Select Requester"
        icon="person-outline"
        value={form.requestedByOption}
        options={REQUESTED_BY_OPTIONS}
        onSelect={(option) => form.setRequestedByOption(option.value)}
      />
      {form.requestedByOption === "Other" && (
        <AppInput placeholder="Enter Name" value={form.requestedByOther} onChangeText={form.setRequestedByOther} />
      )}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
});

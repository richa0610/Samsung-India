import { StyleSheet } from "react-native";

import CompanyField from "@/components/company/CompanyField";
import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { SectionTitle } from "./SectionTitle";
import { AddTrainingForm } from "./useAddTrainingForm";

export function BasicDetailsSection({ form }: { form: AddTrainingForm }) {
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={1} title="Basic Details" icon="document-text-outline" />
      <SearchableSelect
        label="Zone"
        required
        compact
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
        compact
        placeholder={form.zone ? "Select Region" : "Select Zone First"}
        icon="globe-outline"
        value={form.region}
        options={form.regionOptions}
        onSelect={(option) => form.setRegion(option.value)}
        disabled={!form.zone}
      />
      <CompanyField compact value={form.company} />
      <SearchableSelect
        label="Requested By"
        required
        compact
        placeholder="Select Requester"
        icon="person-outline"
        value={form.requestedByOption}
        options={form.requestedByOptions}
        onSelect={(option) => form.setRequestedByOption(option.value)}
      />
      {form.requestedByOption === "Other" && (
        <AppInput compact placeholder="Enter Name" value={form.requestedByOther} onChangeText={form.setRequestedByOther} />
      )}
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
});

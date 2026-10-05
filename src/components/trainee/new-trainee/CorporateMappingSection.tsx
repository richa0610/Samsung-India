import { StyleSheet } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { SectionTitle } from "@/components/training/add-training/SectionTitle";
import { COMPANY_OPTIONS, REGIONS_BY_ZONE, REQUESTED_BY_OPTIONS, ZONES } from "./constants";
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
        options={ZONES.map((z) => ({ label: z, value: z }))}
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
        options={(REGIONS_BY_ZONE[form.zone] ?? []).map((r) => ({ label: r, value: r }))}
        onSelect={(option) => form.setRegion(option.value)}
        disabled={!form.zone}
      />
      <SearchableSelect
        label="Company"
        required
        placeholder="Select Company"
        icon="business-outline"
        value={form.company}
        options={COMPANY_OPTIONS}
        onSelect={(option) => form.setCompany(option.value)}
      />
      <SearchableSelect
        label="Requested By"
        required
        placeholder={form.company ? "Select Requester" : "Select Company First"}
        icon="person-outline"
        value={form.requestedByOption}
        options={form.company ? REQUESTED_BY_OPTIONS : []}
        onSelect={(option) => form.setRequestedByOption(option.value)}
        disabled={!form.company}
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

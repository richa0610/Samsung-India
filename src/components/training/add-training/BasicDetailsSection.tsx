import { StyleSheet } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { SectionTitle } from "./SectionTitle";
import { REGIONS_BY_ZONE, ZONES } from "./constants";
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
        options={ZONES.map((z) => ({ label: z, value: z }))}
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
        options={(REGIONS_BY_ZONE[form.zone] ?? []).map((r) => ({ label: r, value: r }))}
        onSelect={(option) => form.setRegion(option.value)}
        disabled={!form.zone}
      />
      <SearchableSelect
        label="Company"
        required
        compact
        placeholder="Select Company"
        icon="business-outline"
        value={form.company}
        options={[{ label: form.company, value: form.company }]}
        onSelect={() => {}}
        disabled
      />
      <SearchableSelect
        label="Requested By"
        required
        compact
        placeholder={form.company ? "Select Requester" : "Select Company First"}
        icon="person-outline"
        value={form.requestedByOption}
        options={form.company ? form.requestedByOptions : []}
        onSelect={(option) => form.setRequestedByOption(option.value)}
        disabled={!form.company}
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

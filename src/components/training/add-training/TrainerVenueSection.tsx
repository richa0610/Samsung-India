import { StyleSheet } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { STATES } from "@/data/states";
import { SectionTitle } from "./SectionTitle";
import { AddTrainingForm } from "./useAddTrainingForm";

export function TrainerVenueSection({ form }: { form: AddTrainingForm }) {
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={2} title="Trainer & Venue" icon="people-outline" />
      <SearchableSelect
        label="Trainer ID"
        required
        compact
        placeholder="Select Trainer"
        icon="person-circle-outline"
        value={form.trainerId}
        options={form.trainerOptions}
        onSelect={(option) => {
          form.setTrainerId(option.value);
          form.setTrainerName(option.name ?? option.label);
        }}
      />
      <AppInput
        compact
        label="Trainer Name"
        placeholder="Auto-fetched name"
        value={form.trainerName}
        editable={false}
      />
      <SearchableSelect
        label="State"
        required
        compact
        placeholder="Select State"
        icon="map-outline"
        value={form.stateValue}
        options={STATES.map((s) => ({ label: s.label, value: s.value }))}
        onSelect={(option) => {
          form.setStateValue(option.value);
          form.setDistrict("");
          form.setVenue("");
        }}
      />
      <SearchableSelect
        label="District"
        required
        compact
        placeholder={form.stateValue ? "Select District" : "Select State First"}
        icon="location-outline"
        value={form.district}
        options={form.selectedState?.cities ?? []}
        onSelect={(option) => {
          form.setDistrict(option.value);
          form.setVenue("");
        }}
        disabled={!form.stateValue}
      />
      <SearchableSelect
        label="Venue"
        compact
        placeholder={form.district ? "Select Venue" : "Select District First"}
        icon="location-outline"
        value={form.venue}
        options={form.venueOptions}
        onSelect={(option) => form.setVenue(option.value)}
        disabled={!form.district}
      />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
});

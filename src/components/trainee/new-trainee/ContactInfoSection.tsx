import { StyleSheet } from "react-native";

import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { SectionTitle } from "@/components/training/add-training/SectionTitle";
import { STATES } from "@/data/states";
import { digitsOnly } from "@/utils/validation";
import { NewTraineeForm } from "./useNewTraineeForm";

export function ContactInfoSection({ form }: { form: NewTraineeForm }) {
  return (
    <AppCard style={styles.card}>
      <SectionTitle index={4} title="Contact Info" icon="call-outline" />
      <AppInput
        label="Primary Email *"
        placeholder="Enter Your Email ID"
        icon="mail-outline"
        keyboardType="email-address"
        autoCapitalize="none"
        value={form.primaryEmail}
        onChangeText={form.setPrimaryEmail}
      />
      <AppInput
        label="Primary Phone *"
        placeholder="10 Digit Mobile Number"
        icon="call-outline"
        keyboardType="number-pad"
        maxLength={10}
        value={form.primaryPhone}
        onChangeText={(v) => form.setPrimaryPhone(digitsOnly(v))}
      />
      <AppInput
        label="Alt Email"
        placeholder="Optional"
        icon="mail-outline"
        keyboardType="email-address"
        autoCapitalize="none"
        value={form.altEmail}
        onChangeText={form.setAltEmail}
      />
      <AppInput
        label="Alt Phone"
        placeholder="Optional"
        icon="call-outline"
        keyboardType="number-pad"
        maxLength={10}
        value={form.altPhone}
        onChangeText={(v) => form.setAltPhone(digitsOnly(v))}
      />
      <AppInput
        label="Permanent Address"
        placeholder="Full Address"
        icon="location-outline"
        multiline
        value={form.address}
        onChangeText={form.setAddress}
      />
      <SearchableSelect
        label="State"
        required
        placeholder="Select State"
        icon="map-outline"
        value={form.stateValue}
        options={STATES.map((s) => ({ label: s.label, value: s.value }))}
        onSelect={(option) => {
          form.setStateValue(option.value);
          form.setDistrict("");
        }}
      />
      <SearchableSelect
        label="District"
        required
        placeholder={form.stateValue ? "Select District" : "Select State First"}
        icon="location-outline"
        value={form.district}
        options={form.selectedState?.cities ?? []}
        onSelect={(option) => form.setDistrict(option.value)}
        disabled={!form.stateValue}
      />
    </AppCard>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
});

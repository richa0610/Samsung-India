import { Pressable, StyleSheet, View } from "react-native";

import AppText from "@/components/ui/AppText";
import { SearchableSelect, SelectOption } from "@/components/ui/SearchableSelect";
import { STATES } from "@/data/states";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";
import { FilterField, STATE_OPTIONS, TRAINING_TYPE_OPTIONS, ZONE_OPTIONS } from "./leaderboard-filter";

export type LeaderboardFilterValues = {
  trainingType: string;
  state: string;
  district: string;
  zone: string;
};

export type LeaderboardFilterProps = {
  values: LeaderboardFilterValues;
  onChangeValues: (values: LeaderboardFilterValues) => void;
  onApply: () => void;
};

export default function LeaderboardFilter({ values, onChangeValues, onApply }: LeaderboardFilterProps) {
  const updateField = (field: keyof LeaderboardFilterValues, val: string) => {
    onChangeValues({ ...values, [field]: val });
  };

  const districtOptions: SelectOption[] =
    STATES.find((s) => s.label === values.state)?.cities.map((c) => ({ label: c.label, value: c.label })) ?? [];

  return (
    <View style={styles.filterSection}>
      <FilterField label="Training Type :">
        <SearchableSelect
          compact
          containerStyle={styles.selectField}
          placeholder="Select Training Type"
          value={values.trainingType}
          options={TRAINING_TYPE_OPTIONS}
          onSelect={(option) => updateField("trainingType", option.value)}
        />
      </FilterField>

      <View style={styles.twoColRow}>
        <FilterField label="State :" style={styles.col}>
          <SearchableSelect
            compact
            containerStyle={styles.selectField}
            placeholder="Select State"
            value={values.state}
            options={STATE_OPTIONS}
            onSelect={(option) => onChangeValues({ ...values, state: option.value, district: "" })}
          />
        </FilterField>

        <FilterField label="District :" style={styles.col}>
          <SearchableSelect
            compact
            containerStyle={styles.selectField}
            placeholder={values.state ? "Select District" : "Select State First"}
            value={values.district}
            options={districtOptions}
            disabled={!values.state}
            onSelect={(option) => updateField("district", option.value)}
          />
        </FilterField>
      </View>

      <View style={[styles.twoColRow, styles.actionRow]}>
        <FilterField label="Zone :" style={styles.col}>
          <SearchableSelect
            compact
            containerStyle={styles.selectField}
            placeholder="Select Zone"
            value={values.zone}
            options={ZONE_OPTIONS}
            onSelect={(option) => updateField("zone", option.value)}
          />
        </FilterField>

        <View style={[styles.col, styles.buttonCol]}>
          <Pressable style={styles.applyFilterButton} onPress={onApply} accessibilityRole="button" accessibilityLabel="Apply Filter">
            <AppText style={styles.applyFilterButtonText} color={Colors.white} weight={FontWeight.bold}>
              Filter
            </AppText>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  filterSection: {
    backgroundColor: "#EEF5FF",
    borderColor: "#D3E4FF",
    borderWidth: 1,
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
  },
  twoColRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 8,
    alignItems: "flex-end",
  },
  col: {
    flex: 1,
  },
  actionRow: {
    alignItems: "flex-start",
    marginBottom: 0,
  },
  buttonCol: {
    marginTop: 20,
  },
  selectField: {
    marginBottom: 0,
  },
  applyFilterButton: {
    height: 44,
    backgroundColor: "#0066FF",
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  applyFilterButtonText: {
    fontSize: 14.5,
    letterSpacing: 0.5,
  },
});

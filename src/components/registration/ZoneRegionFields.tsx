import { Pressable, StyleSheet, View } from "react-native";
import { Control, Controller, FieldErrors, UseFormSetValue, useWatch } from "react-hook-form";

import AppText from "@/components/ui/AppText";
import InlineSelect from "@/components/ui/InlineSelect";
import { RegisterFormValues } from "@/hooks/useRegisterForm";
import { useZoneRegions } from "@/hooks/useZoneRegions";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";

type ZoneRegionFieldsProps = {
    control: Control<RegisterFormValues>;
    setValue: UseFormSetValue<RegisterFormValues>;
    errors: FieldErrors<RegisterFormValues>;
};

/**
 * Registration only: the trainee's Zone and Region, from the master list. The zone starts their ID
 * (e.g. SOUTH2610001). Both are required while the list has them; if it couldn't be loaded the
 * trainee can still register (the server then gives a TRN... ID) or tap to load it again.
 */
export default function ZoneRegionFields({ control, setValue, errors }: ZoneRegionFieldsProps) {
    const zone = useWatch({ control, name: "zone" });
    const zones = useZoneRegions(zone);

    return (
        <View>
            <View style={styles.row}>
                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="zone"
                        rules={{ validate: (v) => zones.zoneOptions.length === 0 || !!v || "Zone is required" }}
                        render={({ field: { value, onChange } }) => (
                            <InlineSelect
                                placeholder="Select Zone*"
                                value={value}
                                onSelect={(newValue) => {
                                    onChange(newValue);
                                    setValue("region", "");
                                }}
                                options={zones.zoneOptions}
                            />
                        )}
                    />
                </View>

                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="region"
                        rules={{ validate: (v) => zones.regionOptions.length === 0 || !!v || "Region is required" }}
                        render={({ field: { value, onChange } }) => (
                            <InlineSelect
                                placeholder={zone ? "Select Region*" : "Select Zone First"}
                                value={value}
                                disabled={!zone}
                                onSelect={onChange}
                                options={zones.regionOptions}
                            />
                        )}
                    />
                </View>
            </View>
            {errors.zone && <AppText style={styles.error}>{errors.zone.message}</AppText>}
            {errors.region && <AppText style={styles.error}>{errors.region.message}</AppText>}
            {zones.failed && (
                <Pressable onPress={zones.retry} accessibilityRole="button" hitSlop={8}>
                    <AppText style={styles.error}>{"Couldn't load the zone list. Tap to try again."}</AppText>
                </Pressable>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    row: {
        flexDirection: "row",
        alignItems: "flex-start",
        gap: 12,
    },

    half: {
        flex: 1,
    },

    error: {
        color: Colors.danger,
        fontSize: Fonts.bodySm,
        marginTop: -12,
        marginBottom: 12,
    },
});

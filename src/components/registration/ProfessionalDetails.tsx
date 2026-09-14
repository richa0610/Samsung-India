import { useMemo } from "react";
import { View, StyleSheet } from "react-native";
import {
    Control,
    Controller,
    FieldErrors,
    UseFormSetValue,
    useWatch,
} from "react-hook-form";

import AppText from "@/components/ui/AppText";
import AppInput from "@/components/ui/AppInput";
import InlineSelect from "@/components/ui/InlineSelect";
import { STATES } from "@/data/states";

import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { RegisterFormValues } from "@/hooks/useRegisterForm";
import { companyId } from "@/utils/validation/validators";

type ProfessionalDetailsProps = {
    control: Control<RegisterFormValues>;
    setValue: UseFormSetValue<RegisterFormValues>;
    errors: FieldErrors<RegisterFormValues>;
    // Field names that already have a saved value and must stay read-only
    // (Edit Profile lets the trainee fill blanks, not rewrite existing data).
    lockedFields?: Set<keyof RegisterFormValues>;
};

export default function ProfessionalDetails({
    control,
    setValue,
    errors,
    lockedFields,
}: ProfessionalDetailsProps) {
    const locked = (name: keyof RegisterFormValues) => lockedFields?.has(name) ?? false;
    const state = useWatch({ control, name: "state" });
    const selectedState = useMemo(
        () => STATES.find((item) => item.value === state),
        [state]
    );

    return (
        <View>
            <AppText style={styles.sectionTitle}>
                PROFESSIONAL INFO
            </AppText>

            <View style={styles.row}>
                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="designation"
                        rules={{ required: "Designation is required" }}
                        render={({ field: { value, onChange } }) => (
                            <AppInput
                                placeholder="Designation*"
                                autoCapitalize="words"
                                editable={!locked("designation")}
                                value={value}
                                onChangeText={onChange}
                            />
                        )}
                    />
                </View>

                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="employee_id"
                        rules={{ validate: (v) => companyId(v, "Employee ID") ?? true }}
                        render={({ field: { value, onChange } }) => (
                            <AppInput
                                placeholder="Employee ID"
                                autoCapitalize="characters"
                                autoCorrect={false}
                                editable={!locked("employee_id")}
                                value={value}
                                onChangeText={onChange}
                            />
                        )}
                    />
                </View>
            </View>
            {errors.designation && (
                <AppText style={styles.error}>{errors.designation.message}</AppText>
            )}
            {errors.employee_id && (
                <AppText style={styles.error}>{errors.employee_id.message}</AppText>
            )}

            <Controller
                control={control}
                name="supervisorName"
                render={({ field: { value, onChange } }) => (
                    <AppInput
                        placeholder="Supervisor Name"
                        autoCapitalize="words"
                        editable={!locked("supervisorName")}
                        value={value}
                        onChangeText={onChange}
                    />
                )}
            />

            <View style={styles.row}>
                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="state"
                        render={({ field: { value, onChange } }) => (
                            <InlineSelect
                                placeholder="Select State"
                                value={value}
                                disabled={locked("state")}
                                onSelect={(newValue) => {
                                    onChange(newValue);
                                    setValue("district", "");
                                }}
                                options={STATES.map((item) => ({
                                    label: item.label,
                                    value: item.value,
                                }))}
                            />
                        )}
                    />
                </View>

                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="district"
                        render={({ field: { value, onChange } }) => (
                            <InlineSelect
                                placeholder="Select City"
                                value={value}
                                disabled={locked("district")}
                                onSelect={onChange}
                                options={selectedState?.cities || []}
                            />
                        )}
                    />
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    sectionTitle: {
        fontSize: Fonts.bodyLg,
        color: Colors.mainColour1,
        fontWeight: FontWeight.semiBold,
        marginBottom: 10,
        marginTop: 6,
    },

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

import { View, StyleSheet } from "react-native";
import { Control, Controller, FieldErrors } from "react-hook-form";

import AppText from "@/components/ui/AppText";
import AppInput from "@/components/ui/AppInput";
import InlineSelect from "@/components/ui/InlineSelect";

import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { RegisterFormValues } from "@/hooks/useRegisterForm";
import { mobile10 } from "@/utils/validation/validators";

type PersonalDetailsProps = {
    control: Control<RegisterFormValues>;
    errors: FieldErrors<RegisterFormValues>;
    // Field names that already have a saved value and must stay read-only
    // (Edit Profile lets the trainee fill blanks, not rewrite existing data).
    lockedFields?: Set<keyof RegisterFormValues>;
};

export default function PersonalDetails({ control, errors, lockedFields }: PersonalDetailsProps) {
    const locked = (name: keyof RegisterFormValues) => lockedFields?.has(name) ?? false;

    return (
        <View>
            <AppText style={styles.sectionTitle}>
                PERSONAL DETAILS
            </AppText>

            <Controller
                control={control}
                name="name"
                rules={{ required: "Full name is required" }}
                render={({ field: { value, onChange } }) => (
                    <AppInput
                        placeholder="Full Name*"
                        autoCapitalize="words"
                        editable={!locked("name")}
                        value={value}
                        onChangeText={onChange}
                    />
                )}
            />
            {errors.name && (
                <AppText style={styles.error}>{errors.name.message}</AppText>
            )}

            <View style={styles.row}>
                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="phone"
                        rules={{
                            required: "Phone No is required",
                            validate: (v) => mobile10(v, "Phone No") ?? true,
                        }}
                        render={({ field: { value, onChange } }) => (
                            <AppInput
                                placeholder="Phone No*"
                                keyboardType="phone-pad"
                                maxLength={10}
                                editable={!locked("phone")}
                                value={value}
                                onChangeText={onChange}
                            />
                        )}
                    />
                </View>

                <View style={styles.half}>
                    <Controller
                        control={control}
                        name="gender"
                        render={({ field: { value, onChange } }) => (
                            <InlineSelect
                                placeholder="Choose Gender"
                                value={value}
                                disabled={locked("gender")}
                                onSelect={onChange}
                                options={[
                                    { label: "Male", value: "male" },
                                    { label: "Female", value: "female" },
                                    { label: "Other", value: "other" },
                                ]}
                            />
                        )}
                    />
                </View>
            </View>
            {errors.phone && (
                <AppText style={styles.error}>{errors.phone.message}</AppText>
            )}

            <Controller
                control={control}
                name="email"
                rules={{
                    required: "Email is required",
                    pattern: {
                        value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                        message: "Enter a valid email",
                    },
                }}
                render={({ field: { value, onChange } }) => (
                    <AppInput
                        placeholder="Email*"
                        keyboardType="email-address"
                        autoCapitalize="none"
                        autoCorrect={false}
                        editable={!locked("email")}
                        value={value}
                        onChangeText={onChange}
                    />
                )}
            />
            {errors.email && (
                <AppText style={styles.error}>{errors.email.message}</AppText>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    sectionTitle: {
        fontSize: Fonts.bodyLg,
        color: Colors.mainColour1,
        fontWeight: FontWeight.semiBold,
        marginBottom: 10,
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

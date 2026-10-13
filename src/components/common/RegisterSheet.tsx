import { ScrollView, View, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import PersonalDetails from "@/components/registration/PersonalDetails";
import ProfessionalDetails from "@/components/registration/ProfessionalDetails";
import RegisterButton from "@/components/registration/RegisterButton";
import SecurityFooter from "@/components/common/SecurityFooter";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { useRegisterForm } from "@/hooks/useRegisterForm";

type RegisterSheetProps = {
    visible: boolean;
    onClose: () => void;
    // Set when registering as part of a scanned-QR session join.
    joinCode?: string;
};


export default function RegisterSheet({
    visible,
    onClose,
    joinCode,
}: RegisterSheetProps) {
    const router = useRouter();
    // Registering signs the trainee in (no password to log in with later), so
    // they go straight on - to the scanned session (QR join) or the trainee
    // home - the same places the login form sends them.
    const { control, errors, setValue, onSubmit, loading, error } = useRegisterForm({
        joinCode,
        onSuccess: () => {
            onClose();
            router.replace(joinCode ? "/session" : ("/session_detail" as any));
        },
    });

    return (
        <AppModal
            visible={visible}
            title="Participant Registration"
            subtitle="Secure onboarding for this session"
            onClose={onClose}
            position="bottom"
            contentStyle={{
                paddingHorizontal: 20,
                paddingTop: 20,
                paddingBottom: 40,
            }}
        >
            <View style={styles.divider} />

            <ScrollView
                showsVerticalScrollIndicator={false}
                contentContainerStyle={styles.formContent}
            >
                <PersonalDetails control={control} errors={errors} />
                <ProfessionalDetails control={control} setValue={setValue} errors={errors} />

                {error && (
                    <AppText style={styles.error}>{error}</AppText>
                )}

                <RegisterButton onPress={onSubmit} loading={loading} />

                <View style={styles.securityFooter}>
                    <SecurityFooter />
                </View>
            </ScrollView>
        </AppModal>
    );
}

const styles = StyleSheet.create({
    formContent: {
        paddingBottom: 4,
    },
    securityFooter: {
        marginTop: 22,
    },

    divider: {
        height: 1,
        backgroundColor: Colors.inputColour2,
        // opacity: .2,
        marginVertical: 16,
    },

    error: {
        color: Colors.danger,
        fontSize: Fonts.bodySm,
        marginBottom: 12,
        textAlign: "center",
    },
});

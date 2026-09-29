import { View, StyleSheet, Image } from "react-native";

import AppText from "../ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { Radius } from "@/theme/radius";

type Props = {
    title?: string;
    subtitle?: string;
};

export default function AuthHeader({ title, subtitle }: Props) {
    return (
        <View style={styles.container}>
            <View style={[styles.iconContainer, title && styles.iconContainerWithText]}>
                <Image
                    source={require("@/assets/images/Icons/user_icon.png")}
                    style={styles.icon}
                    resizeMode="contain"
                    tintColor="#E8F0FF"
                />
            </View>
            {title && (
                <AppText weight="500" style={styles.title} color={Colors.white}>
                    {title}
                </AppText>
            )}
            {subtitle && (
                <AppText color={Colors.white} style={styles.subtitle}>
                    {subtitle}
                </AppText>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: Colors.mainColour1,
        paddingVertical: 32,
        paddingHorizontal: 35,
        borderTopLeftRadius: Radius.xxl,
        borderTopRightRadius: Radius.xxl,
    },
    iconContainer: {
        borderRadius: 45,
        backgroundColor: "#E8F0FF",
        justifyContent: "center",
        alignItems: "center",
    },
    iconContainerWithText: {
        marginBottom: 16,
    },
    icon: {
        width: Fonts.profileIconSize,
        height: Fonts.profileIconSize,
        backgroundColor: Colors.mainColour1,
        borderRadius: 45,
    },
    title: {
        marginBottom: 6,
        fontSize: Fonts.h1,
    },
    subtitle: {
        textAlign: "center",
        fontSize: Fonts.xs,
    },
});

import { Pressable, ScrollView, StyleSheet, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Ionicons } from "@expo/vector-icons";
import { useRouter } from "expo-router";
import { StatusBar } from "expo-status-bar";

import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Shadows } from "@/theme/shadows";
import {
  BasicDetailsSection,
  ChecklistSection,
  SessionFlowSection,
  TrainerVenueSection,
  TrainingDetailsSection,
  useAddTrainingForm,
} from "@/components/training/add-training";

export default function AddTrainingScreen() {
  const router = useRouter();
  const form = useAddTrainingForm();

  return (
    <>
      <StatusBar style="dark" />
      <SafeAreaView style={styles.container} edges={["top", "bottom"]}>
        <View style={styles.header}>
          <Pressable style={styles.backButton} onPress={() => router.back()} hitSlop={8}>
            <Ionicons name="arrow-back" size={20} color={Colors.mainColour1} />
          </Pressable>
          <View style={styles.headerTextGroup}>
            <AppText style={styles.headerTitle} weight={FontWeight.semiBold}>Training Registration</AppText>
            <AppText style={styles.headerSubtitle} color={Colors.gray600}>
              Fill in the details to register a new training.
            </AppText>
          </View>
        </View>

        <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
          <BasicDetailsSection form={form} />
          <TrainerVenueSection form={form} />
          <TrainingDetailsSection form={form} />
          <SessionFlowSection form={form} />
          <ChecklistSection form={form} />
        </ScrollView>
      </SafeAreaView>
    </>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: Colors.background },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  backButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: Colors.white,
    alignItems: "center",
    justifyContent: "center",
    ...Shadows.card,
  },
  headerTextGroup: { flex: 1 },
  headerTitle: { fontSize: Fonts.h3 },
  headerSubtitle: { fontSize: Fonts.bodySm, marginTop: 2 },
  content: { flexGrow: 1, padding: 16, paddingTop: 4, paddingBottom: 32, gap: 14 },
});

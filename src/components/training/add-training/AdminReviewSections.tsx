import { useState } from "react";
import { ActivityIndicator, Linking, Pressable, StyleSheet, TextInput, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppButton from "@/components/ui/AppButton";
import AppCard from "@/components/ui/AppCard";
import AppInput from "@/components/ui/AppInput";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import MediaImage from "@/components/ui/MediaImage";
import { SearchableSelect } from "@/components/ui/SearchableSelect";
import { useAuth } from "@/hooks/useAuth";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import { Spacing } from "@/theme/spacing";
import { digitsOnly } from "@/utils/validation";
import { downloadAndPrint } from "@/utils/downloadMedia";
import { resolveMediaUrl } from "@/utils/media";
import { SectionTitle } from "./SectionTitle";
import { AddTrainingForm } from "./useAddTrainingForm";

const APPROVAL_OPTIONS = ["Pending", "Approved", "Rejected"].map((v) => ({ label: v, value: v }));
// "Started" is what the admin sees for a running session (stored as Ongoing).
const TRAINING_STATUS_OPTIONS = [
  { label: "Scheduled", value: "Scheduled" },
  { label: "Started", value: "Ongoing" },
  { label: "Completed", value: "Completed" },
  { label: "Cancelled", value: "Cancelled" },
];

function EvidenceTile({
  icon,
  title,
  path,
  isImage,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  path?: string;
  isImage: boolean;
}) {
  const { adminToken } = useAuth();
  const url = resolveMediaUrl(path);
  const looksLikeImage = isImage || /\.(jpe?g|png|webp)$/i.test(path ?? "");
  const [downloading, setDownloading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);

  const handleDownload = async () => {
    if (!url || downloading) return;
    setDownloading(true);
    try {
      await downloadAndPrint(
        url,
        (path ?? title).split("/").pop() ?? title,
        adminToken ? { Authorization: `Bearer ${adminToken}` } : undefined,
      );
    } catch {
      // print dialog dismissed or download failed - nothing to surface
    } finally {
      setDownloading(false);
    }
  };

  return (
    <View style={styles.evidenceTile}>
      <View style={styles.evidenceHeader}>
        <View style={styles.evidenceIcon}>
          <Ionicons name={icon} size={16} color="#4F46E5" />
        </View>
        <View style={styles.evidenceText}>
          <AppText style={styles.evidenceTitle} weight={FontWeight.semiBold}>
            {title}
          </AppText>
          {url ? (
            <View style={styles.actionRow}>
              <Pressable
                style={[styles.actionPill, styles.viewPill]}
                onPress={() => (looksLikeImage ? setPreviewVisible(true) : Linking.openURL(url))}
                accessibilityRole={looksLikeImage ? "button" : "link"}
                accessibilityLabel={`View ${title}`}
              >
                <AppText style={styles.actionText} color={Colors.white} weight={FontWeight.bold}>
                  View
                </AppText>
              </Pressable>
              <Pressable
                style={[styles.actionPill, styles.downloadPill]}
                onPress={handleDownload}
                accessibilityRole="button"
                accessibilityLabel={`Download ${title}`}
              >
                {downloading ? (
                  <ActivityIndicator size="small" color={Colors.white} />
                ) : (
                  <AppText style={styles.actionText} color={Colors.white} weight={FontWeight.bold}>
                    Download
                  </AppText>
                )}
              </Pressable>
            </View>
          ) : (
            <AppText style={styles.evidenceMissing} color={Colors.gray400}>
              Not available
            </AppText>
          )}
        </View>
      </View>
      {url && looksLikeImage && (
        <Pressable onPress={() => setPreviewVisible(true)}>
          <MediaImage path={path} style={styles.evidenceImage} contentFit="cover" />
        </Pressable>
      )}

      {url && looksLikeImage && (
        <AppModal
          visible={previewVisible}
          onClose={() => setPreviewVisible(false)}
          title={title}
          showCloseButton
          contentStyle={styles.previewModalContent}
        >
          <MediaImage path={path} style={styles.previewImage} contentFit="contain" />
        </AppModal>
      )}
    </View>
  );
}

export function AdminReviewSections({ form }: { form: AddTrainingForm }) {
  const decisionChanged = form.approvalStatus !== form.originalApproval && form.approvalStatus !== "Pending";

  return (
    <>
      <AppCard style={styles.card}>
        <SectionTitle index={6} title="Post-Training Data" icon="clipboard-outline" />
        <AppInput
          compact
          label="Attendance Sheet PAX (Actual)"
          value={form.attendanceSheetPax}
          editable={false}
          labelColor={Colors.success}
        />
        <AppInput
          compact
          label="Confirmed Pax (Admin)"
          placeholder="Enter confirmed pax count"
          keyboardType="number-pad"
          maxLength={6}
          value={form.confirmedPax}
          onChangeText={(v) => form.setConfirmedPax(digitsOnly(v))}
          labelColor={Colors.danger}
        />
        <SearchableSelect
          label="Approval Status"
          compact
          icon="shield-checkmark-outline"
          value={form.approvalStatus}
          options={APPROVAL_OPTIONS}
          onSelect={(option) => form.setApprovalStatus(option.value as typeof form.approvalStatus)}
        />
        <SearchableSelect
          label="Training Status"
          compact
          icon="pulse-outline"
          value={form.trainingStatus}
          options={TRAINING_STATUS_OPTIONS}
          onSelect={(option) => form.setTrainingStatus(option.value as typeof form.trainingStatus)}
        />
      </AppCard>

      <AppCard style={styles.card}>
        <SectionTitle index={7} title="Session Evidence" icon="images-outline" />
        <EvidenceTile icon="document-text" title="Attendance Sheet" path={form.evidence.attendanceSheet} isImage={false} />
        <EvidenceTile icon="log-in-outline" title="Trainer Check-in" path={form.evidence.checkInPhoto} isImage />
        <EvidenceTile icon="log-out-outline" title="Trainer Check-out" path={form.evidence.checkOutPhoto} isImage />
      </AppCard>

      <AppCard style={styles.card}>
        <AppText style={styles.messageLabel} weight={FontWeight.medium}>
          Any Message{decisionChanged ? " *" : ""}
        </AppText>
        <TextInput
          style={styles.messageInput}
          value={form.adminMessage}
          onChangeText={form.setAdminMessage}
          placeholder={decisionChanged ? `Why is this training being ${form.approvalStatus.toLowerCase()}?` : "Add a note for the trainer"}
          placeholderTextColor={Colors.gray400}
          multiline
          textAlignVertical="top"
          maxLength={500}
        />

        <Pressable style={styles.checkboxRow} onPress={() => form.setAdminConfirm((v) => !v)}>
          <View style={[styles.checkbox, form.adminConfirm && styles.checkboxChecked]}>
            {form.adminConfirm && <Ionicons name="checkmark" size={12} color={Colors.white} />}
          </View>
          <AppText style={styles.checkboxLabel}>I confirm the details above are correct.</AppText>
        </Pressable>

        {form.notice && <AppText style={styles.notice}>{form.notice}</AppText>}

        <AppButton title="Update Training Session" onPress={form.handleSubmit} loading={form.submitting} />
      </AppCard>
    </>
  );
}

const styles = StyleSheet.create({
  card: { padding: 16 },
  evidenceTile: {
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xxl,
    padding: 10,
    marginBottom: Spacing.md,
    gap: 8,
  },
  evidenceHeader: { flexDirection: "row", alignItems: "center", gap: 10 },
  evidenceIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: "#EEF2FF",
    alignItems: "center",
    justifyContent: "center",
  },
  evidenceText: { flex: 1, gap: 1 },
  evidenceTitle: { fontSize: Fonts.bodySm },
  evidenceMissing: { fontSize: Fonts.overline },
  actionRow: { flexDirection: "row", gap: 6, marginTop: 2 },
  actionPill: { borderRadius: 4, paddingHorizontal: 9, paddingVertical: 3, minWidth: 44, alignItems: "center" },
  viewPill: { backgroundColor: "#3B4FE4" },
  downloadPill: { backgroundColor: Colors.gray800 },
  actionText: { fontSize: 10 },
  evidenceImage: { width: "100%", height: 150, borderRadius: Radius.xl, backgroundColor: Colors.gray200 },
  previewModalContent: { width: "92%", padding: 0, overflow: "hidden" },
  previewImage: { width: "100%", height: 420, backgroundColor: Colors.black },
  messageLabel: { fontSize: Fonts.body, marginBottom: Spacing.sm },
  messageInput: {
    minHeight: 110,
    borderWidth: 1,
    borderColor: Colors.gray200,
    borderRadius: Radius.xl,
    padding: Spacing.md,
    fontSize: Fonts.bodySm,
    color: Colors.black,
    backgroundColor: Colors.white,
    marginBottom: Spacing.lg,
  },
  checkboxRow: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: Spacing.lg },
  checkbox: {
    width: 18,
    height: 18,
    borderRadius: 4,
    borderWidth: 1,
    borderColor: Colors.gray400,
    alignItems: "center",
    justifyContent: "center",
  },
  checkboxChecked: { backgroundColor: Colors.mainColour1, borderColor: Colors.mainColour1 },
  checkboxLabel: { fontSize: Fonts.body, flex: 1 },
  notice: { color: Colors.danger, fontSize: Fonts.bodySm, textAlign: "center", marginBottom: 12 },
});

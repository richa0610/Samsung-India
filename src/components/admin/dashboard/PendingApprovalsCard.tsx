import { StyleSheet, View } from "react-native";

import { PendingSessionItem } from "@/api/training";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { Fonts } from "@/theme/fonts";
import { FontWeight } from "@/theme/fontWeight";
import { Radius } from "@/theme/radius";
import DashboardSectionCard from "./DashboardSectionCard";
import PendingApprovalRow from "./PendingApprovalRow";

type PendingApprovalsCardProps = {
  pending: PendingSessionItem[];
  loading: boolean;
  actioningUid: string | null;
  onApprove: (uid: string) => void;
  onReject: (uid: string) => void;
};

export default function PendingApprovalsCard({
  pending,
  loading,
  actioningUid,
  onApprove,
  onReject,
}: PendingApprovalsCardProps) {
  return (
    <DashboardSectionCard
      icon="checkmark-done-circle-outline"
      title="Pending Approvals"
      badge={
        pending.length > 0 && (
          <View style={styles.countBadge}>
            <AppText style={styles.countBadgeText} color={Colors.white} weight={FontWeight.bold}>
              {pending.length}
            </AppText>
          </View>
        )
      }
      loading={loading}
      isEmpty={pending.length === 0}
      emptyIcon="checkmark-circle-outline"
      emptyText="Nothing waiting on review."
    >
      <View style={styles.pendingList}>
        {pending.map((item) => (
          <PendingApprovalRow
            key={item.conferenceUid}
            item={item}
            isActioning={actioningUid === item.conferenceUid}
            onApprove={onApprove}
            onReject={onReject}
          />
        ))}
      </View>
    </DashboardSectionCard>
  );
}

const styles = StyleSheet.create({
  countBadge: {
    backgroundColor: Colors.danger,
    borderRadius: Radius.pill,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  countBadgeText: { fontSize: Fonts.overline },
  pendingList: { marginTop: 10, gap: 10 },
});

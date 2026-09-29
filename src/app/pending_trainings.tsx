import { useRouter } from "expo-router";

import { TrainingListView, pendingStatusColumn } from "@/components/training/TrainingListView";
import { usePagedTrainingList } from "@/hooks/usePagedTrainingList";

export default function PendingTrainingsScreen() {
  const router = useRouter();
  // This trainer's own trainings awaiting review, a page at a time.
  const paged = usePagedTrainingList(true);

  return (
    <TrainingListView
      title="Pending Training List"
      subtitle="View and manage all trainings"
      items={paged.items}
      loading={paged.loading}
      refreshing={paged.refreshing}
      onRefresh={paged.refresh}
      paged={paged}
      onBack={() => router.back()}
      onEdit={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid } })}
      statusColumn={pendingStatusColumn()}
      exportFileName="pending-training-list"
      emptyLabel="No pending trainings. Everything you've scheduled has already been reviewed by an admin."
    />
  );
}

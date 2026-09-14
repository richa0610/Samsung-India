import { useRouter } from "expo-router";

import { TrainingListView, pendingStatusColumn } from "@/components/training/TrainingListView";
import { useTrainerAgendaList } from "@/hooks/useTrainerAgendaList";

export default function PendingTrainingsScreen() {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useTrainerAgendaList(true);

  return (
    <TrainingListView
      title="Pending Training List"
      subtitle="View and manage all trainings"
      items={items}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
      onBack={() => router.back()}
      onEdit={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid } })}
      statusColumn={pendingStatusColumn()}
      exportFileName="pending-training-list"
      emptyLabel="No pending trainings. Everything you've scheduled has already been reviewed by an admin."
    />
  );
}

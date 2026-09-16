import { useRouter } from "expo-router";

import { TrainingListView, conferenceStatusColumn } from "@/components/training/TrainingListView";
import { useTrainerAgendaList } from "@/hooks/useTrainerAgendaList";

export default function TrainingListScreen() {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useTrainerAgendaList(false);

  return (
    <TrainingListView
      title="Training List"
      subtitle="View and manage all trainings"
      items={items}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
      onBack={() => router.back()}
      onEdit={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid } })}
      statusColumn={conferenceStatusColumn()}
      exportFileName="training-list"
      emptyLabel="No trainings yet. Sessions show up here once an admin approves them - check Pending Training List until then."
    />
  );
}

import { useRouter } from "expo-router";

import TrainerListFilterBar, { TRAINER_LIST_FILTERS } from "@/components/trainer/TrainerListFilterBar";
import { TrainingListView, conferenceStatusColumn } from "@/components/training/TrainingListView";
import { usePagedTrainingList } from "@/hooks/usePagedTrainingList";

export default function TrainingListScreen() {
  const router = useRouter();
  // This trainer's own approved trainings, a page at a time; the server authorizes, searches, sorts and pages.
  const paged = usePagedTrainingList(false, "approved", TRAINER_LIST_FILTERS);

  return (
    <TrainingListView
      title="Training List"
      subtitle="View and manage all trainings"
      items={paged.items}
      loading={paged.loading}
      refreshing={paged.refreshing}
      onRefresh={paged.refresh}
      paged={paged}
      onBack={() => router.back()}
      topContent={<TrainerListFilterBar />}
      onEdit={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid } })}
      statusColumn={conferenceStatusColumn()}
      exportFileName="training-list"
      emptyLabel="No approved trainings in these dates. Change the range above, or check Pending Training List for sessions an admin hasn't approved yet."
    />
  );
}

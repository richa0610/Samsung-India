import { useRouter } from "expo-router";

import TrainerListFilterBar, { TRAINER_LIST_FILTERS } from "@/components/trainer/TrainerListFilterBar";
import { TrainingListView, pendingStatusColumn } from "@/components/training/TrainingListView";
import { usePagedTrainingList } from "@/hooks/usePagedTrainingList";

export default function PendingTrainingsScreen() {
  const router = useRouter();
  // This trainer's own trainings awaiting review, a page at a time.
  const paged = usePagedTrainingList(true, "approved", TRAINER_LIST_FILTERS);

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
      topContent={<TrainerListFilterBar />}
      onEdit={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid } })}
      statusColumn={pendingStatusColumn()}
      exportFileName="pending-training-list"
      emptyLabel="No pending trainings in these dates - everything scheduled in them has been reviewed. Change the range above to see other dates."
    />
  );
}

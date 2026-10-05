import { useRouter } from "expo-router";

import TrainerListFilterBar, { TRAINER_LIST_FILTERS } from "@/components/trainer/TrainerListFilterBar";
import { TraineeListView } from "@/components/trainee/TraineeListView";
import { usePagedTraineeList } from "@/hooks/usePagedTraineeList";

export default function PendingTraineeScreen() {
  const router = useRouter();
  // Only trainees awaiting approval, a page at a time.
  const paged = usePagedTraineeList(true, TRAINER_LIST_FILTERS);

  return (
    <TraineeListView
      title="Pending Trainee List"
      subtitle="View and manage all trainee"
      items={paged.items}
      loading={paged.loading}
      refreshing={paged.refreshing}
      onRefresh={paged.refresh}
      paged={paged}
      onBack={() => router.back()}
      topContent={<TrainerListFilterBar />}
      exportFileName="pending-trainee-list"
      emptyLabel="No pending trainees registered in these dates. Change the range above to see other dates."
    />
  );
}

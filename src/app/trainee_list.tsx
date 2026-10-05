import { useRouter } from "expo-router";

import TrainerListFilterBar, { TRAINER_LIST_FILTERS } from "@/components/trainer/TrainerListFilterBar";
import { TraineeListView } from "@/components/trainee/TraineeListView";
import { usePagedTraineeList } from "@/hooks/usePagedTraineeList";

export default function TraineeListScreen() {
  const router = useRouter();
  // The trainees this account may see, a page at a time; the server authorizes, searches, sorts and pages.
  const paged = usePagedTraineeList(false, TRAINER_LIST_FILTERS);

  return (
    <TraineeListView
      title="Trainee List"
      subtitle="View and manage all trainee"
      items={paged.items}
      loading={paged.loading}
      refreshing={paged.refreshing}
      onRefresh={paged.refresh}
      paged={paged}
      onBack={() => router.back()}
      topContent={<TrainerListFilterBar />}
      exportFileName="trainee-list"
      emptyLabel="No trainees registered in these dates. Change the range above to see trainees registered earlier."
    />
  );
}

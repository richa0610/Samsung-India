import { useRouter } from "expo-router";

import { TraineeListView } from "@/components/trainee/TraineeListView";
import { usePagedTraineeList } from "@/hooks/usePagedTraineeList";

export default function PendingTraineeScreen() {
  const router = useRouter();
  // Only trainees awaiting approval, a page at a time.
  const paged = usePagedTraineeList(true);

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
      exportFileName="pending-trainee-list"
      emptyLabel="No pending trainees. Everything registered so far has already been reviewed."
    />
  );
}

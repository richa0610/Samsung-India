import { useRouter } from "expo-router";

import { TraineeListView } from "@/components/trainee/TraineeListView";
import { useTraineeList } from "@/hooks/useTraineeList";

export default function PendingTraineeScreen() {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useTraineeList(true);

  return (
    <TraineeListView
      title="Pending Trainee List"
      subtitle="View and manage all trainee"
      items={items}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
      onBack={() => router.back()}
      onEdit={() => router.push("/session_dashboard")}
      exportFileName="pending-trainee-list"
      emptyLabel="No pending trainees. Everything registered so far has already been reviewed."
    />
  );
}

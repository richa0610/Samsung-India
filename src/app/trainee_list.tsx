import { useRouter } from "expo-router";

import { TraineeListView } from "@/components/trainee/TraineeListView";
import { useTraineeList } from "@/hooks/useTraineeList";

export default function TraineeListScreen() {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useTraineeList(false);

  return (
    <TraineeListView
      title="Trainee List"
      subtitle="View and manage all trainee"
      items={items}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
      onBack={() => router.back()}
      onEdit={() => router.push("/session_dashboard")}
      exportFileName="trainee-list"
      emptyLabel="No trainees yet. Trainees you register will show up here, approved or not."
    />
  );
}

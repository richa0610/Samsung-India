import { useRouter } from "expo-router";

import TrainerListFilterBar, { TRAINER_LIST_FILTERS } from "@/components/trainer/TrainerListFilterBar";
import { AttendanceListView } from "@/components/attendance/AttendanceListView";
import { usePagedAttendanceList } from "@/hooks/usePagedAttendanceList";

export default function PendingAttendanceScreen() {
  const router = useRouter();
  // Attendance on this trainer's own trainings, a page at a time; the server authorizes, splits, searches and pages.
  const paged = usePagedAttendanceList("pending", TRAINER_LIST_FILTERS);

  return (
    <AttendanceListView
      title="Pending Attendance List"
      subtitle="View and manage all attendance"
      items={paged.items}
      loading={paged.loading}
      refreshing={paged.refreshing}
      onRefresh={paged.refresh}
      paged={paged}
      onBack={() => router.back()}
      topContent={<TrainerListFilterBar />}
      exportFileName="pending-attendance-list"
      emptyLabel="No pending attendance for trainings in these dates."
    />
  );
}

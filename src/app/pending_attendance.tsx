import { useRouter } from "expo-router";

import { AttendanceListView } from "@/components/attendance/AttendanceListView";
import { useAttendanceList } from "@/hooks/useAttendanceList";

export default function PendingAttendanceScreen() {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useAttendanceList("pending");

  return (
    <AttendanceListView
      title="Pending Attendance List"
      subtitle="View and manage all attendance"
      items={items}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
      onBack={() => router.back()}
      onViewCandidate={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceId ?? "" } })}
      exportFileName="pending-attendance-list"
      emptyLabel="No pending attendance. Everyone has been marked."
    />
  );
}

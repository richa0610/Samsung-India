import { useRouter } from "expo-router";

import { AttendanceListView } from "@/components/attendance/AttendanceListView";
import { useAttendanceList } from "@/hooks/useAttendanceList";

export default function ConfirmedAttendanceScreen() {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useAttendanceList("confirmed");

  return (
    <AttendanceListView
      title="Confirmed Attendance List"
      subtitle="View and manage all attendance"
      items={items}
      loading={loading}
      refreshing={refreshing}
      onRefresh={refresh}
      onBack={() => router.back()}
      onViewCandidate={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceId ?? "" } })}
      exportFileName="confirmed-attendance-list"
      emptyLabel="No confirmed attendance yet."
    />
  );
}

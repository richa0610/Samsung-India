import AdminAttendanceScreen from "@/components/admin/AdminAttendanceScreen";

export default function AdminPendingAttendanceScreen() {
  return (
    <AdminAttendanceScreen
      mode="pending"
      title="Pending Attendance"
      subtitle="Participants not yet marked"
      exportFileName="pending-attendance-list"
      emptyLabel="No pending attendance."
    />
  );
}

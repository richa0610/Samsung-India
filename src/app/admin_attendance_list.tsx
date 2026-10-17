import AdminAttendanceScreen from "@/components/admin/AdminAttendanceScreen";

export default function AdminAttendanceListScreen() {
  return (
    <AdminAttendanceScreen
      mode="all"
      title="Attendance List"
      subtitle="Attendance across every trainer's trainings"
      exportFileName="attendance-list"
      emptyLabel="No attendance records yet."
    />
  );
}

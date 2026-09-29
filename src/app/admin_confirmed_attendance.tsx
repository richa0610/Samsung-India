import AdminAttendanceScreen from "@/components/admin/AdminAttendanceScreen";

export default function AdminConfirmedAttendanceScreen() {
  return (
    <AdminAttendanceScreen
      mode="confirmed"
      title="Confirmed Attendance"
      subtitle="Participants marked present or absent"
      exportFileName="confirmed-attendance-list"
      emptyLabel="No confirmed attendance yet."
    />
  );
}

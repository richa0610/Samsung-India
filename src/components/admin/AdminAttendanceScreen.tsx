import { useRouter } from "expo-router";

import AdminFilterBar from "@/components/admin/AdminFilterBar";
import { AdminTabBar } from "@/components/admin/dashboard";
import { AttendanceListView } from "@/components/attendance/AttendanceListView";
import { useAdminAttendanceColumns } from "@/components/attendance/attendance-list/useAdminAttendanceColumns";
import { useAttendanceList } from "@/hooks/useAttendanceList";

type AdminAttendanceScreenProps = {
  mode: "all" | "pending" | "confirmed";
  title: string;
  subtitle: string;
  exportFileName: string;
  emptyLabel: string;
};

/** Org-wide attendance table for admins - one screen, three filtered views. */
export default function AdminAttendanceScreen({ mode, title, subtitle, exportFileName, emptyLabel }: AdminAttendanceScreenProps) {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useAttendanceList(mode, true);
  const columns = useAdminAttendanceColumns((row) => {
    if (row.conferenceId) {
      router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceId } });
    }
  });

  return (
    <>
      <AttendanceListView
        title={title}
        subtitle={subtitle}
        items={items}
        loading={loading}
        refreshing={refreshing}
        onRefresh={refresh}
        onBack={() => router.back()}
        exportFileName={exportFileName}
        emptyLabel={emptyLabel}
        columns={columns}
        hasBottomNav
        topContent={<AdminFilterBar />}
      />
      <AdminTabBar activeTab="attendance" />
    </>
  );
}

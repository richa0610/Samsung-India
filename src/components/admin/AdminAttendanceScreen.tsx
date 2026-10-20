import { useRouter } from "expo-router";

import AdminFilterBar from "@/components/admin/AdminFilterBar";
import { AdminTabBar } from "@/components/admin/dashboard";
import { AttendanceListView } from "@/components/attendance/AttendanceListView";
import { useAdminAttendanceColumns } from "@/components/attendance/attendance-list/useAdminAttendanceColumns";
import { usePagedAttendanceList } from "@/hooks/usePagedAttendanceList";

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
  // Loaded a page at a time; the server does the mode split, searching, sorting and paging.
  const paged = usePagedAttendanceList(mode);
  const columns = useAdminAttendanceColumns((row) => {
    if (row.conferenceId) {
      router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceId, from: "admin" } });
    }
  });

  return (
    <>
      <AttendanceListView
        title={title}
        subtitle={subtitle}
        items={paged.items}
        loading={paged.loading}
        refreshing={paged.refreshing}
        onRefresh={paged.refresh}
        paged={paged}
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

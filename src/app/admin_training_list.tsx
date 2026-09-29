import { useRouter } from "expo-router";

import AdminFilterBar from "@/components/admin/AdminFilterBar";
import { AdminTabBar } from "@/components/admin/dashboard";
import { TrainingListView, conferenceStatusColumn } from "@/components/training/TrainingListView";
import { usePagedTrainingList } from "@/hooks/usePagedTrainingList";

export default function AdminTrainingListScreen() {
  const router = useRouter();
  // Loaded 50 rows at a time; the server does the searching, sorting and paging.
  const paged = usePagedTrainingList(false);

  return (
    <>
      <TrainingListView
        title="Training List"
        subtitle="All reviewed trainings across every trainer"
        items={paged.items}
        loading={paged.loading}
        refreshing={paged.refreshing}
        onRefresh={paged.refresh}
        paged={paged}
        onBack={() => router.back()}
        onEdit={(row) => router.push({ pathname: "/edit_training", params: { conferenceUid: row.conferenceUid } })}
        onReport={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid, from: "admin" } })}
        extendedColumns
        hasBottomNav
        topContent={<AdminFilterBar />}
        statusColumn={conferenceStatusColumn()}
        exportFileName="training-list"
        emptyLabel="No reviewed trainings yet."
      />
      <AdminTabBar activeTab="training" />
    </>
  );
}

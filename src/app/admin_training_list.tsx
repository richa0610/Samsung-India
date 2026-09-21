import { useRouter } from "expo-router";

import AdminFilterBar from "@/components/admin/AdminFilterBar";
import { AdminTabBar } from "@/components/admin/dashboard";
import { TrainingListView, conferenceStatusColumn } from "@/components/training/TrainingListView";
import { useTrainerAgendaList } from "@/hooks/useTrainerAgendaList";

export default function AdminTrainingListScreen() {
  const router = useRouter();
  const { items, loading, refreshing, refresh } = useTrainerAgendaList(false, true);

  return (
    <>
      <TrainingListView
        title="Training List"
        subtitle="All reviewed trainings across every trainer"
        items={items}
        loading={loading}
        refreshing={refreshing}
        onRefresh={refresh}
        onBack={() => router.back()}
        onEdit={(row) => router.push({ pathname: "/edit_training", params: { conferenceUid: row.conferenceUid } })}
        onReport={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid } })}
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

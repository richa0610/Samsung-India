import { useRouter } from "expo-router";

import AdminFilterBar from "@/components/admin/AdminFilterBar";
import { AdminTabBar } from "@/components/admin/dashboard";
import { TrainingListView, pendingStatusColumn } from "@/components/training/TrainingListView";
import { usePagedTrainingList } from "@/hooks/usePagedTrainingList";

// Every trainer's Pending training org-wide, in the same table as the admin
// Training List. Tapping a row opens the review page, where the admin approves
// or rejects with a message.
export default function AdminPendingTrainingsScreen() {
  const router = useRouter();
  // Loaded 50 rows at a time; the server does the searching, sorting and paging.
  const paged = usePagedTrainingList(true);

  const openReview = (row: { conferenceUid: string }) =>
    router.push({ pathname: "/edit_training", params: { conferenceUid: row.conferenceUid } });

  return (
    <>
      <TrainingListView
        title="Pending Training"
        subtitle="Trainings awaiting your review"
        items={paged.items}
        loading={paged.loading}
        refreshing={paged.refreshing}
        onRefresh={paged.refresh}
        paged={paged}
        onBack={() => router.back()}
        onEdit={openReview}
        onReport={(row) => router.push({ pathname: "/session_dashboard", params: { conferenceUid: row.conferenceUid } })}
        extendedColumns
        hasBottomNav
        topContent={<AdminFilterBar />}
        statusColumn={pendingStatusColumn()}
        exportFileName="pending-trainings"
        emptyLabel="Nothing waiting on review right now."
      />
      <AdminTabBar activeTab="training" />
    </>
  );
}

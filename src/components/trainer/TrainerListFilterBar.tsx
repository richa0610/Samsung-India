import AdminFilterBar from "@/components/admin/AdminFilterBar";
import { AdminFilterScope } from "@/hooks/useAdminFilters";

/** The filter every list in the trainer's flow shares - the 1st of this month to today (IST) until the trainer
 *  picks another range (see useAdminFilters). Pass it to the list's paging hook. */
export const TRAINER_LIST_FILTERS: AdminFilterScope = "trainerLists";

/** The date filter shown above every list in the trainer's flow (Training, Attendance and
 *  Trainee lists): just the From/To range. */
export default function TrainerListFilterBar() {
  return <AdminFilterBar scope={TRAINER_LIST_FILTERS} dateOnly />;
}

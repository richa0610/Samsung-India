import { DashboardTrainingRow } from "@/api/session";
import { TrainingRowData } from "./TrainingDetailsTable";

/** Maps the `/sessions/dashboard` rows onto the table component's shape.
 * `null` scores/ranks become the "-" sentinel the table renders as a dash. */
export function toTrainingRows(rows: DashboardTrainingRow[]): TrainingRowData[] {
  return rows.map((row) => ({
    id: row.conferenceUid,
    status: row.status,
    date: row.date ?? "",
    day: row.day ?? "",
    postTestScore: row.postTestScore ?? "-",
    quizScore: row.quizScore ?? "-",
    ranking: row.rank ?? "-",
    rankingScope: (row.rankScope as TrainingRowData["rankingScope"]) ?? undefined,
    isLiveOrScheduled: row.status === "Ongoing" || row.status === "Scheduled",
  }));
}

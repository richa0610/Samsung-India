import { DataTableColumn } from "@/components/ui/DataTable";
import { StatusPill, StatusTone } from "@/components/ui/StatusPill";
import { TrainingAgendaItem } from "@/api/training";

export function pendingStatusColumn(): DataTableColumn<TrainingAgendaItem> {
  return {
    key: "status",
    header: "Status",
    minWidth: 92,
    render: () => <StatusPill label="Pending" tone="warning" />,
    exportValue: () => "Pending",
  };
}

const CONFERENCE_STATUS_PRESENTATION: Record<string, { label: string; tone: StatusTone }> = {
  Ongoing: { label: "Started", tone: "success" },
  Scheduled: { label: "Scheduled", tone: "warning" },
  Completed: { label: "Completed", tone: "neutral" },
};

// A training's status is only meaningful once an admin has approved it -
// until then it shows as Pending regardless of `conferenceStatus` (which
// defaults to "Scheduled" the moment it's created, before any review).
function presentationFor(row: TrainingAgendaItem): { label: string; tone: StatusTone } {
  if (row.approvalStatus !== "Approved") {
    return { label: "Pending", tone: "warning" };
  }
  return (
    CONFERENCE_STATUS_PRESENTATION[row.conferenceStatus] ?? {
      label: row.conferenceStatus,
      tone: "neutral" as StatusTone,
    }
  );
}

export function conferenceStatusColumn(): DataTableColumn<TrainingAgendaItem> {
  return {
    key: "status",
    header: "Status",
    minWidth: 92,
    render: (row) => {
      const presentation = presentationFor(row);
      return <StatusPill label={presentation.label} tone={presentation.tone} />;
    },
    exportValue: (row) => presentationFor(row).label,
  };
}

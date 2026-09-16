import { StatusTone } from "@/components/ui/StatusPill";

export const APPROVAL_STATUS_PRESENTATION: Record<string, { label: string; tone: StatusTone }> = {
  Pending: { label: "Pending", tone: "warning" },
  Approved: { label: "Approved", tone: "success" },
  Rejected: { label: "Rejected", tone: "danger" },
};

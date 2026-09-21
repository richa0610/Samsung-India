// A training/module's internal status string ("Scheduled") stays as-is for
// filtering/comparisons - this only maps it to clearer user-facing wording
// wherever it's actually shown. Shared by the Training Details table and the
// Training Detail screen so both describe the same status the same way.
const TRAINING_STATUS_LABELS: Record<string, string> = {
  Scheduled: "Not Started",
};

export function trainingStatusLabel(status: string): string {
  return TRAINING_STATUS_LABELS[status] ?? status;
}

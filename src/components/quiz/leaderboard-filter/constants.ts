import { SelectOption } from "@/components/ui/SearchableSelect";
import { STATES } from "@/data/states";

export const TRAINING_TYPE_OPTIONS: SelectOption[] = ["Classroom Training", "Webinar", "Product Training"].map((v) => ({
  label: v,
  value: v,
}));
export const ZONE_OPTIONS: SelectOption[] = ["North", "South", "East", "West"].map((v) => ({ label: v, value: v }));
export const STATE_OPTIONS: SelectOption[] = STATES.map((s) => ({ label: s.label, value: s.label }));

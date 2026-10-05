import { SelectOption } from "@/components/ui/SearchableSelect";
import { COMPANY_OPTIONS, REGIONS_BY_ZONE, REQUESTED_BY_OPTIONS, ZONES } from "@/components/training/add-training/constants";

export { COMPANY_OPTIONS, REGIONS_BY_ZONE, REQUESTED_BY_OPTIONS, ZONES };

export const AGENCY_OPTIONS: SelectOption[] = [
  { label: "Quess Corp Ltd", value: "Quess Corp Ltd" },
  { label: "Adecco India", value: "Adecco India" },
  { label: "TeamLease Services", value: "TeamLease Services" },
  { label: "Randstad India", value: "Randstad India" },
];

export const DESIGNATION_OPTIONS: SelectOption[] = [
  "Sales Executive",
  "Sales Associate",
  "Team Leader",
  "Store Manager",
  "Area Manager",
  "Zonal Manager",
  "Regional Manager",
  "Trainer",
  "Other",
].map((v) => ({ label: v, value: v }));

export const SUPERVISOR_DESIGNATION_OPTIONS: SelectOption[] = [
  "Team Leader",
  "Store Manager",
  "Area Manager",
  "Zonal Manager",
  "Regional Manager",
  "Other",
].map((v) => ({ label: v, value: v }));

export const GENDER_OPTIONS: SelectOption[] = ["Male", "Female", "Other"].map((v) => ({ label: v, value: v }));

export const JOB_STATUS_OPTIONS: SelectOption[] = ["Active", "Inactive", "On Leave", "Resigned"].map((v) => ({
  label: v,
  value: v,
}));

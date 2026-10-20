import { SearchableSelect } from "@/components/ui/SearchableSelect";

type CompanyFieldProps = {
  /** The company's name, as shown. */
  value: string;
  compact?: boolean;
};

/** A record's company on a form (a training, a new trainee) - shown, never chosen: it is the
 *  company of the tenant the user is signed in to, and the server sets it (user, 2026-10-18). */
export default function CompanyField({ value, compact }: CompanyFieldProps) {
  return (
    <SearchableSelect
      label="Company"
      required
      compact={compact}
      placeholder="Company"
      icon="business-outline"
      value={value}
      options={value ? [{ label: value, value }] : []}
      onSelect={() => {}}
      disabled
    />
  );
}

import Calendar from "@/components/calendar/Calendar";
import {
  DatePreset,
  DateRange,
  formatDMY,
  rangeForPreset,
} from "@/components/calendar/calendarUtils";

export type { DateRange, DatePreset };
export { rangeForPreset, formatDMY };

type DateDropProps = {
  range: DateRange;
  preset: DatePreset;
  onApply: (range: DateRange, preset: DatePreset) => void;
};

export default function DateDrop({ range, preset, onApply }: DateDropProps) {
  return (
    <Calendar
      range={range}
      preset={preset}
      onApply={onApply}
    />
  );
}

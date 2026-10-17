import { useState } from "react";

export function useMonthYear(initialDate: Date) {
  const [month, setMonth] = useState<number>(initialDate.getMonth());
  const [year, setYear] = useState<number>(initialDate.getFullYear());

  const prevMonth = () => {
    if (month === 0) {
      setMonth(11);
      setYear((y) => y - 1);
    } else {
      setMonth((m) => m - 1);
    }
  };

  const nextMonth = () => {
    if (month === 11) {
      setMonth(0);
      setYear((y) => y + 1);
    } else {
      setMonth((m) => m + 1);
    }
  };

  return { month, year, setMonth, setYear, prevMonth, nextMonth };
}

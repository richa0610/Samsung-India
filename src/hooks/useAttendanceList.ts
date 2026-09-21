/**
 * useAttendanceList Hook
 * Shared by Attendance List, Pending Attendance and Confirmed Attendance -
 * fetches this trainer's attendance report with support for filtering to
 * pending/confirmed only, plus focus effect, pull-to-refresh, and a live
 * "attendance_marked" push while focused.
 */

import { useCallback, useState } from "react";
import { useFocusEffect } from "expo-router";
import { useAuth } from "@/hooks/useAuth";
import { AttendanceListItem, fetchAttendanceList } from "@/api/attendanceList";
import { useAdminFilters } from "@/hooks/useAdminFilters";
import { subscribe } from "@/services/liveEvents";

export function useAttendanceList(mode: "all" | "pending" | "confirmed" = "all", org = false) {
  const { adminToken } = useAuth();
  const { applied, appliedKey } = useAdminFilters("lists");
  const [items, setItems] = useState<AttendanceListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(
    async (loadMode: "load" | "refresh" | "silent" = "load") => {
      if (!adminToken) return;
      if (loadMode === "refresh") setRefreshing(true);
      else if (loadMode === "load") setLoading(true);
      try {
        const data = await fetchAttendanceList(adminToken, org, org ? applied : undefined);
        setItems(
          mode === "pending"
            ? data.filter((item) => !item.marked)
            : mode === "confirmed"
              ? data.filter((item) => item.marked)
              : data,
        );
      } catch {
        if (loadMode !== "silent") setItems([]);
      } finally {
        if (loadMode === "refresh") setRefreshing(false);
        else if (loadMode === "load") setLoading(false);
      }
    },
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `appliedKey` is `applied`, serialised so an equal filter doesn't refetch
    [adminToken, mode, org, appliedKey],
  );

  useFocusEffect(
    useCallback(() => {
      load();
      const unsubscribe = subscribe("attendance_marked", () => load("silent"));
      return unsubscribe;
    }, [load]),
  );

  return {
    items,
    loading,
    refreshing,
    refresh: () => load("refresh"),
  };
}

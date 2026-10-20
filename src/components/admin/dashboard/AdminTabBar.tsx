import { useCallback, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";

import { fetchPendingTrainingCount } from "@/api/training";
import { useAuth } from "@/hooks/useAuth";
import AdminBottomNav, { AdminDashboardTab } from "./AdminBottomNav";

const TAB_ROUTES: Partial<Record<AdminDashboardTab, "/admin_dashboard">> = {
  home: "/admin_dashboard",
};

type AdminTabBarProps = {
  /** The tab this screen belongs under (e.g. the review page sits under "training"). */
  activeTab: AdminDashboardTab;
};

/** Self-contained admin bottom nav for secondary screens (detail, edit, builder)
 *  that don't already own the dashboard data - loads just the pending count for
 *  the badge and handles tab navigation itself. */
export default function AdminTabBar({ activeTab }: AdminTabBarProps) {
  const router = useRouter();
  const { adminToken } = useAuth();
  const [pendingCount, setPendingCount] = useState(0);

  useFocusEffect(
    useCallback(() => {
      if (!adminToken) return;
      let cancelled = false;
      fetchPendingTrainingCount(adminToken)
        .then((count) => {
          if (!cancelled) setPendingCount(count);
        })
        .catch(() => {});
      return () => {
        cancelled = true;
      };
    }, [adminToken]),
  );

  return (
    <AdminBottomNav
      activeTab={activeTab}
      pendingCount={pendingCount}
      onSelectTab={(tab) => {
        const route = TAB_ROUTES[tab];
        if (route) router.replace(route);
      }}
    />
  );
}

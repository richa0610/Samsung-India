/**
 * useAdminDashboard Hook
 * Manages admin dashboard data fetching, approving/rejecting sessions,
 * loading/refreshing states, and action states.
 */

import { useCallback, useState } from "react";
import { useFocusEffect, useRouter } from "expo-router";
import { useAuth } from "@/hooks/useAuth";
import {
  ApiError,
  AssessmentSuiteOut,
  PendingSessionItem,
  approveTraining,
  fetchAssessmentSuites,
  fetchPendingTrainings,
  rejectTraining,
} from "@/api/training";

export function useAdminDashboard() {
  const router = useRouter();
  const { admin, adminToken, adminLogout } = useAuth();

  const [pending, setPending] = useState<PendingSessionItem[]>([]);
  const [suites, setSuites] = useState<AssessmentSuiteOut[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [actioningUid, setActioningUid] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (isRefresh = false) => {
      if (!adminToken) return;
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      setError(null);
      try {
        const [pendingList, suiteList] = await Promise.all([
          fetchPendingTrainings(adminToken),
          fetchAssessmentSuites(adminToken),
        ]);
        setPending(pendingList);
        setSuites(suiteList);
      } catch (err) {
        setError(
          err instanceof ApiError
            ? err.message
            : "Couldn't load the admin dashboard.",
        );
      } finally {
        if (isRefresh) {
          setRefreshing(false);
        } else {
          setLoading(false);
        }
      }
    },
    [adminToken],
  );

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const handleApprove = async (uid: string) => {
    if (!adminToken || actioningUid) return;
    setActioningUid(uid);
    try {
      await approveTraining(adminToken, uid);
      await load();
    } catch {
      setError("Couldn't approve this session.");
    } finally {
      setActioningUid(null);
    }
  };

  const handleReject = async (uid: string) => {
    if (!adminToken || actioningUid) return;
    setActioningUid(uid);
    try {
      await rejectTraining(adminToken, uid);
      await load();
    } catch {
      setError("Couldn't reject this session.");
    } finally {
      setActioningUid(null);
    }
  };

  const handleLogout = () => {
    adminLogout();
    router.replace("/trainer_login");
  };

  return {
    admin,
    pending,
    suites,
    loading,
    refreshing,
    actioningUid,
    error,
    refresh: () => load(true),
    handleApprove,
    handleReject,
    handleLogout,
  };
}

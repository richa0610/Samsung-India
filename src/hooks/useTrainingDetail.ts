import { useFocusEffect, useLocalSearchParams, useRouter } from "expo-router";
import { useCallback, useState } from "react";

import { ApiError } from "@/api/client";
import { TrainingDetail, getTrainingDetail } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";

export function useTrainingDetail() {
  const router = useRouter();
  const params = useLocalSearchParams<{ conferenceUid?: string }>();
  const { token } = useAuth();

  const [detail, setDetail] = useState<TrainingDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Which module cards are expanded to show their question review - closed
  // by default so the screen opens as a scannable summary, not a wall of text.
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(new Set());

  const load = useCallback(async () => {
    if (!token || !params.conferenceUid) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getTrainingDetail(token, params.conferenceUid);
      setDetail(data);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't load this training's details.");
    } finally {
      setLoading(false);
    }
  }, [token, params.conferenceUid]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const toggleModule = (key: string) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  return {
    onBack: () => router.back(),
    detail,
    loading,
    error,
    reload: load,
    expandedKeys,
    toggleModule,
  };
}

import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchZoneRegions } from "@/api/locations";
import type { MasterGroup } from "@/api/training";
import { zoneKey } from "@/utils/zones";

export type ZoneOption = { label: string; value: string };

const asOptions = (names: string[]): ZoneOption[] => names.map((name) => ({ label: name, value: name }));

/**
 * The Zone and Region pickers of the trainee registration form, from the master list
 * (GET /locations/zones - no sign-in needed). The Region options are the chosen zone's own; a zone
 * matches in either spelling ("North" / "North Zone"). The zone starts the trainee's ID.
 */
export function useZoneRegions(zone: string) {
  const [groups, setGroups] = useState<MasterGroup[]>([]);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    fetchZoneRegions()
      .then((data) => {
        if (!active) return;
        setGroups(data);
        setFailed(false);
      })
      .catch(() => {
        if (!active) return;
        setGroups([]);
        setFailed(true);
      });
    return () => {
      active = false;
    };
  }, [attempt]);

  const retry = useCallback(() => setAttempt((count) => count + 1), []);
  const zoneGroup = groups.find((group) => zoneKey(group.name) === zoneKey(zone));
  const zoneOptions = useMemo(() => asOptions(groups.map((group) => group.name)), [groups]);
  const regionOptions = useMemo(() => asOptions(zoneGroup?.options ?? []), [zoneGroup]);

  return {
    zoneOptions,
    regionOptions,
    /** The list couldn't be loaded (e.g. no connection) - `retry` asks again. */
    failed,
    retry,
  };
}

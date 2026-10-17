import { useCallback, useEffect, useMemo, useState } from "react";

import { fetchStateDistricts } from "@/api/locations";
import type { MasterGroup } from "@/api/training";
import { findPlace } from "@/utils/places";

export type PlaceOption = { label: string; value: string };

const asOptions = (names: string[]): PlaceOption[] => names.map((name) => ({ label: name, value: name }));
const groupName = (group: MasterGroup) => group.name;
const itself = (name: string) => name;

/**
 * The State and District pickers, from the pincode directory (GET /locations/states) - one list
 * for the trainee registration / Edit Profile form, the New Trainee form and Add Training. The
 * District options are the chosen state's own districts.
 *
 * `shownState` / `shownDistrict`: a saved value in another spelling ("uttar_pradesh",
 * "UTTAR PRADESH") as the directory spells it ("Uttar Pradesh") - what a form shows and saves.
 * A value the directory doesn't have is kept as it is.
 */
export function useStateDistricts(state: string, district: string) {
  const [groups, setGroups] = useState<MasterGroup[]>([]);
  const [failed, setFailed] = useState(false);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let active = true;
    fetchStateDistricts()
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
  const stateGroup = findPlace(groups, state, groupName);
  const stateOptions = useMemo(() => asOptions(groups.map(groupName)), [groups]);
  const districtOptions = useMemo(() => asOptions(stateGroup?.options ?? []), [stateGroup]);

  return {
    stateOptions,
    districtOptions,
    shownState: stateGroup?.name ?? state,
    shownDistrict: findPlace(stateGroup?.options ?? [], district, itself) ?? district,
    /** The list couldn't be loaded (e.g. no connection) - `retry` asks again. */
    failed,
    retry,
  };
}

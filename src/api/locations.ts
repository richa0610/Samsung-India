import { apiRequest } from "./client";
import type { MasterGroup } from "./training";

/** Every state with its districts, from the pincode directory. Needs no sign-in - the trainee
 *  registration form shows it before anyone has logged in; the staff forms use it too. */
export function fetchStateDistricts() {
  return apiRequest<MasterGroup[]>("/locations/states");
}

/** Every zone with its regions, from the master list - for the trainee registration form (needs no
 *  sign-in). The zone starts the trainee's ID (e.g. SOUTH2610001). */
export function fetchZoneRegions() {
  return apiRequest<MasterGroup[]>("/locations/zones");
}

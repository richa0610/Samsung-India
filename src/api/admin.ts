import { AdminFilters, adminFilterParams } from "./adminFilters";
import { apiRequest } from "./client";
import { Company } from "@/config/company";
import { getDeviceId, getDeviceName } from "@/config/device";

export type AdminAccount = {
  username: string;
  name: string;
  role: string;
  offerId?: string | null;
  company?: string | null;
  tenant_id?: string | null;
  profilePicture?: string | null;
};

export type AdminAuthSession = {
  access_token: string;
  token_type: string;
  admin: AdminAccount;
  // The company signed in to - set when the sign-in named none (the server found it).
  company?: Company | null;
};

/** What `loginAdmin` answers (409, code CHOOSE_COMPANY) for an admin with access to several
 *  companies: the list to pick from, and a short-lived ticket for `chooseLoginCompany`. */
export type CompanyChoice = {
  code: "CHOOSE_COMPANY";
  message: string;
  companies: Company[];
  ticket: string;
};

/** A trainer by username, HO ID or phone, or an admin by username - no company code (the server
 *  finds it) - and this device, which counts toward a trainer's device limit. */
export function loginAdmin(username: string, password: string) {
  return apiRequest<AdminAuthSession>(
    "/admin/login",
    { method: "POST", body: JSON.stringify({ username, password, deviceId: getDeviceId(), deviceName: getDeviceName() }) },
    { company: false },
  );
}

/** Signs in an admin with several companies to the one they picked, with the ticket `loginAdmin`
 *  answered with. */
export function chooseLoginCompany(ticket: string, tenantId: string) {
  return apiRequest<AdminAuthSession>(
    "/admin/login/company",
    { method: "POST", body: JSON.stringify({ ticket, tenantId }) },
    { company: false },
  );
}

export type TrainingTypeStatusCount = {
  status: string;
  count: number;
};

export type TrainingTypeGroup = {
  type: string;
  statuses: TrainingTypeStatusCount[];
};

export type AudienceStatusItem = {
  label: string;
  count: number;
  color?: string | null;
};

export type AudienceSection = {
  title: string;
  items: AudienceStatusItem[];
};

export type TrainerStatusItem = {
  label: string;
  count: number;
};

export type TrainerStatusSection = {
  title: string;
  items: TrainerStatusItem[];
};

export type AssessmentGapItem = {
  label: string;
  value: string;
  color?: string | null;
};

export type AssessmentGapSection = {
  title: string;
  items: AssessmentGapItem[];
};

export type AdminDashboardStats = {
  training: {
    planned: number;
    completed: number;
    pending: number;
    ratePercent: number;
    typeBreakdown?: TrainingTypeGroup[];
  };
  audience: {
    participants: number;
    present: number;
    absent: number;
    presentPercent: number;
    absentPercent: number;
    typeBreakdown?: AudienceSection[];
  };
  trainers: {
    pool: number;
    inTraining: number;
    idle: number;
    utilizationPercent: number;
    statusAnalysis?: TrainerStatusSection[];
  };
  assessment: {
    attempts: number;
    passCount: number;
    failCount: number;
    avgPercent: number;
    eligibilityGaps?: AssessmentGapSection[];
  };
};

/** `fresh` skips the server's 30-second cache - for pull-to-refresh and live "something changed" updates. */
export function fetchAdminDashboardStats(token: string, filters?: AdminFilters, options?: { fresh?: boolean }) {
  const params = new URLSearchParams(adminFilterParams(filters));
  if (options?.fresh) params.set("fresh", "true");
  const query = params.toString();
  return apiRequest<AdminDashboardStats>(`/admin/dashboard/stats${query ? `?${query}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

/** The caller's own admin_access grant - which zones/regions their account is authorized for,
 *  so the Training/Attendance filter panel can hide the rest. Display only: `null` means "not
 *  restricted on that axis", a list means "only these" (already lower-cased/trimmed, the same
 *  form the filter query params use). It grants nothing by itself - every request that actually
 *  reads or changes a training is still checked server-side regardless of what this returns. */
export type AdminAccessScope = {
  allowed: boolean;
  isSuper: boolean;
  role: string | null;
  zones: string[] | null;
  regions: string[] | null;
};

export function fetchAdminAccessScope(token: string) {
  return apiRequest<AdminAccessScope>("/admin/access/scope", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

/** The tenant's trainee security check-in settings. Super Admin only - anyone else gets a 403. */
export type CheckInSettings = {
  /** Trainees pass a face check before the photo (true), or just capture it (false). */
  faceDetectionEnabled: boolean;
};

export function fetchCheckInSettings(token: string) {
  return apiRequest<CheckInSettings>("/admin/settings/check-in", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export function updateCheckInSettings(token: string, settings: CheckInSettings) {
  return apiRequest<CheckInSettings>("/admin/settings/check-in", {
    method: "PUT",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify(settings),
  });
}

export { ApiError } from "./client";

/** Signs the admin / trainer out on the server: every token issued for them stops working (all devices). */
export function logoutAdmin(token: string) {
  return apiRequest<null>("/admin/logout", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

import { USE_MOCK_DATA } from "@/config/dataSource";
import { AdminFilters, adminFilterParams } from "./adminFilters";
import { apiRequest } from "./client";
import * as mock from "./mockService";

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
};

export function loginAdmin(username: string, password: string) {
  if (USE_MOCK_DATA) return mock.loginAdmin(username, password);
  return apiRequest<AdminAuthSession>("/admin/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
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

export { ApiError } from "./client";

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

export function fetchAdminDashboardStats(token: string, filters?: AdminFilters) {
  const params = new URLSearchParams(adminFilterParams(filters));
  const query = params.toString();
  return apiRequest<AdminDashboardStats>(`/admin/dashboard/stats${query ? `?${query}` : ""}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
}

export { ApiError } from "./client";

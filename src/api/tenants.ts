import { apiRequest } from "./client";
import { Company } from "@/config/company";

/** The active company a typed company code (its tenant ID, any letter case) names - 404 "Company
 *  code not found" for an unknown code or a suspended company. Public: it runs before sign-in. */
export function lookupCompany(code: string) {
  return apiRequest<Company>(`/tenants/lookup?code=${encodeURIComponent(code.trim())}`);
}

/** The company the given token was issued for. */
export function fetchCurrentCompany(token: string) {
  return apiRequest<Company>("/tenants/current", {
    headers: { Authorization: `Bearer ${token}` },
  });
}

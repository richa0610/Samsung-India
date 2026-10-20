import { persistedText } from "./persistedText";

/**
 * The company (tenant) this device signs in to - chosen once by typing its company code, which the
 * server confirms (GET /tenants/lookup), and kept until the person changes it. Signing out keeps it.
 *
 * Read synchronously at module load, like the server URL, so the very first request already
 * carries it: `client.ts` sends `tenantId` as X-Tenant-ID on every request (the server only uses
 * it before sign-in - after that, the token's own tenant wins). Screens follow changes through
 * `useCompany` (subscribe / getCompany).
 */
export type Company = {
  tenantId: string;
  companyName: string;
};

const store = persistedText("company.json");
const listeners = new Set<() => void>();

function parse(raw: string | null): Company | null {
  if (!raw) return null;
  try {
    const value = JSON.parse(raw) as Partial<Company>;
    return value.tenantId && value.companyName ? { tenantId: value.tenantId, companyName: value.companyName } : null;
  } catch {
    return null;
  }
}

let current: Company | null = parse(store.read());

export function getCompany(): Company | null {
  return current;
}

export function setCompany(company: Company): void {
  current = { tenantId: company.tenantId, companyName: company.companyName };
  store.write(JSON.stringify(current));
  listeners.forEach((listener) => listener());
}

export function subscribeCompany(listener: () => void): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

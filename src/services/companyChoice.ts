import { CompanyChoice } from "@/api/admin";

/**
 * The companies an admin may pick from after signing in without a company code, and the ticket that
 * signs them in to one - handed from the staff login to the choose-company page. Kept in memory only:
 * the ticket lasts two minutes, and an app restart starts the sign-in again.
 */
let pending: CompanyChoice | null = null;

export function setCompanyChoice(choice: CompanyChoice | null): void {
  pending = choice;
}

export function getCompanyChoice(): CompanyChoice | null {
  return pending;
}

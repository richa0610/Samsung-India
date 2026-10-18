import { useState } from "react";

import { useCompany } from "@/hooks/useCompany";

import CompanyBadge from "./CompanyBadge";
import CompanyCodeForm from "./CompanyCodeForm";

type CompanyGateProps = {
  children: React.ReactNode;
};

/**
 * The company code is mandatory before signing in (user, 2026-10-18): until this device has a
 * company, the gate shows the company code form instead of `children` (e.g. a QR join preview).
 * Once it has one, it shows the company badge (with Change) above them. The first screen has its
 * own full-page version of this step - CompanyCodeScreen.
 */
export default function CompanyGate({ children }: CompanyGateProps) {
  const company = useCompany();
  const [changing, setChanging] = useState(false);
  const stopChanging = () => setChanging(false);

  if (!company || changing) {
    return <CompanyCodeForm onDone={stopChanging} onCancel={company ? stopChanging : undefined} />;
  }

  return (
    <>
      <CompanyBadge company={company} onChange={() => setChanging(true)} />
      {children}
    </>
  );
}

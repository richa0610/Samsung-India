import { useState } from "react";

import { useCompany } from "@/hooks/useCompany";

import CompanyBadge from "./CompanyBadge";
import CompanyCodeForm from "./CompanyCodeForm";

type CompanyGateProps = {
  children: React.ReactNode;
};

/**
 * Where a company must be known before anyone has signed in - registering without a QR code, or an
 * old QR code that names none (user, 2026-10-19; signing in finds the company itself): until this
 * device has a company, the gate shows the company code form instead of `children`. Once it has one,
 * it shows the company badge (with Change) above them.
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

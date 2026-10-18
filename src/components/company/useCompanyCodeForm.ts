import { useState } from "react";

import { ApiError } from "@/api/client";
import { lookupCompany } from "@/api/tenants";
import { setCompany } from "@/config/company";
import { COMPANY_TEXT } from "@/constants/strings";

/** The company code form: the server confirms the code (GET /tenants/lookup) before the device is
 *  tied to that company - an unknown code never becomes the saved company. */
export function useCompanyCodeForm(onDone?: () => void) {
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    const typed = code.trim();
    if (!typed) {
      setError(COMPANY_TEXT.required);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setCompany(await lookupCompany(typed));
      setCode("");
      onDone?.();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const changeCode = (value: string) => {
    setCode(value);
    if (error) setError(null);
  };

  return { code, changeCode, error, loading, submit };
}

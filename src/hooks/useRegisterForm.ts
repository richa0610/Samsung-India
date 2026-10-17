import { useState } from "react";
import { useForm } from "react-hook-form";

import { ApiError, registerTrainee } from "@/api/auth";
import { joinSession } from "@/api/session";
import { useAuth } from "@/hooks/useAuth";

export type RegisterFormValues = {
  name: string;
  phone: string;
  email: string;
  gender: string;
  designation: string;
  employee_id: string;
  supervisorName: string;
  state: string;
  district: string;
  // Registration only (ZoneRegionFields) - the zone starts the trainee's ID.
  zone: string;
  region: string;
};

const defaultValues: RegisterFormValues = {
  name: "",
  phone: "",
  email: "",
  gender: "",
  designation: "",
  employee_id: "",
  supervisorName: "",
  state: "",
  district: "",
  zone: "",
  region: "",
};

type UseRegisterFormOptions = {
  // Registration always signs the new trainee in (they have no password to
  // log in with later). When set (QR-join flow), it also binds them to this
  // session before `onSuccess` fires.
  joinCode?: string;
  onSuccess?: () => void;
};

export function useRegisterForm({ joinCode, onSuccess }: UseRegisterFormOptions = {}) {
  const { setSession } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    setValue,
    reset,
    formState: { errors },
  } = useForm<RegisterFormValues>({ defaultValues });

  const onSubmit = handleSubmit(async (values) => {
    setLoading(true);
    setError(null);
    try {
      const session = await registerTrainee({
        name: values.name.trim(),
        phone: values.phone.trim(),
        email: values.email.trim(),
        gender: values.gender || undefined,
        designation: values.designation || undefined,
        employee_id: values.employee_id || undefined,
        supervisorName: values.supervisorName || undefined,
        state: values.state,
        district: values.district || undefined,
        zone: values.zone || undefined,
        region: values.region || undefined,
      });

      setSession(session);
      if (joinCode) {
        try {
          await joinSession(joinCode, session.access_token, true);
        } catch {
          // Non-fatal - they still land on /session.
        }
      }

      reset(defaultValues);
      onSuccess?.();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
    }
  });

  return { control, errors, setValue, onSubmit, loading, error };
}

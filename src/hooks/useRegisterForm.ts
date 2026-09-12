import { useState } from "react";
import { useForm } from "react-hook-form";

import { ApiError, loginTrainee, registerTrainee } from "@/api/auth";
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
};

type UseRegisterFormOptions = {
  // When set (QR-join flow), a successful registration also signs the new
  // trainee in and binds them to this session before `onSuccess` fires.
  // Plain registration (no code) keeps the old behaviour: register only,
  // then the user logs in themselves.
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
      const phone = values.phone.trim();
      await registerTrainee({
        name: values.name.trim(),
        phone,
        email: values.email.trim(),
        gender: values.gender || undefined,
        designation: values.designation || undefined,
        employee_id: values.employee_id || undefined,
        supervisorName: values.supervisorName || undefined,
        state: values.state || undefined,
        district: values.district || undefined,
      });

      if (joinCode) {
        const session = await loginTrainee(phone);
        setSession(session);
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

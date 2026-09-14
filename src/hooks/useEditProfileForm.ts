import { useState } from "react";
import { useForm } from "react-hook-form";

import { ApiError, updateTrainee } from "@/api/auth";
import { useAuth } from "@/hooks/useAuth";
import type { RegisterFormValues } from "@/hooks/useRegisterForm";

type UseEditProfileFormOptions = {
  onSuccess?: () => void;
};

export function useEditProfileForm({ onSuccess }: UseEditProfileFormOptions = {}) {
  const { trainee, token, setSession } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const defaultValues: RegisterFormValues = {
    name: trainee?.name ?? "",
    phone: trainee?.phone ? String(trainee.phone) : "",
    email: trainee?.email ?? "",
    gender: trainee?.gender ?? "",
    designation: trainee?.designation ?? "",
    employee_id: trainee?.employee_id ?? "",
    supervisorName: trainee?.supervisorName ?? "",
    state: trainee?.state ?? "",
    district: trainee?.district ?? "",
  };

  // The trainee may only fill in blanks - any field that already came back
  // with a saved value is shown read-only.
  const lockedFields = new Set(
    (Object.keys(defaultValues) as (keyof RegisterFormValues)[]).filter(
      (key) => defaultValues[key].trim() !== "",
    ),
  );

  const {
    control,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormValues>({ defaultValues });

  const onSubmit = handleSubmit(async (values) => {
    if (!token) {
      setError("Your session has expired. Please log in again.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const session = await updateTrainee(token, {
        name: values.name.trim(),
        phone: values.phone.trim(),
        email: values.email.trim(),
        gender: values.gender || undefined,
        designation: values.designation || undefined,
        employee_id: values.employee_id || undefined,
        supervisorName: values.supervisorName || undefined,
        state: values.state || undefined,
        district: values.district || undefined,
      });
      setSession(session);
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

  return { control, errors, setValue, onSubmit, loading, error, lockedFields };
}

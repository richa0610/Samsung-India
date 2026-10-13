import { apiRequest, apiUpload } from "./client";

// Field names mirror the `trainee` table from the legacy database dump.
export type Trainee = {
  id: number;
  traineeUid: string;
  name: string;
  phone: number;
  email: string;
  gender: string | null;
  designation: string | null;
  employee_id: string | null;
  supervisorName: string | null;
  state: string | null;
  district: string | null;
  profilePhoto: string | null;
  status: string;
  workZone?: string | null;
  departmentSupport?: string | null;
  department?: string | null;
  sessionCode?: string | null;
};

export type AuthSession = {
  access_token: string;
  token_type: string;
  trainee: Trainee;
};

export type RegisterPayload = {
  name: string;
  phone: string;
  email: string;
  gender?: string;
  designation?: string;
  employee_id?: string;
  supervisorName?: string;
  state: string;
  district?: string;
};

/** Self-registration (no password) also signs the new trainee in - it returns their session. */
export function registerTrainee(payload: RegisterPayload) {
  return apiRequest<AuthSession>("/trainees/register", {
    method: "POST",
    body: JSON.stringify({ ...payload, phone: Number(payload.phone) }),
  });
}

/** `identifier` is what the trainee typed as Company ID / Phone No: Trainee UID, username or phone. */
export function loginTrainee(identifier: string, password: string) {
  return apiRequest<AuthSession>("/trainees/login", {
    method: "POST",
    body: JSON.stringify({ identifier, password }),
  });
}

/** Signs the trainee out on the server: every token issued for them stops working (all devices). */
export function logoutTrainee(token: string) {
  return apiRequest<null>("/trainees/logout", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
}

export type UpdateProfilePayload = Partial<{
  name: string;
  phone: string;
  email: string;
  gender: string;
  designation: string;
  employee_id: string;
  supervisorName: string;
  state: string;
  district: string;
}>;

export function updateTrainee(token: string, payload: UpdateProfilePayload) {
  return apiRequest<AuthSession>("/trainees/me", {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({
      ...payload,
      phone: payload.phone ? Number(payload.phone) : undefined,
    }),
  });
}

export type PickedImage = {
  uri: string;
  name: string;
  type: string;
};

export function uploadTraineePhoto(token: string, image: PickedImage) {
  const formData = new FormData();
  formData.append("file", {
    uri: image.uri,
    name: image.name,
    type: image.type,
  } as unknown as Blob);

  return apiUpload<Trainee>("/trainees/me/photo", formData, token);
}

export { ApiError } from "./client";

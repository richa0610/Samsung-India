import { apiRequest, apiUpload } from "./client";
import { Company } from "@/config/company";
import { getDeviceId, getDeviceName } from "@/config/device";

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
  // Optional: a session saved on the phone before these were sent has none until the next sign-in.
  supervisorDesignation?: string | null;
  state: string | null;
  district: string | null;
  zone?: string | null;
  region?: string | null;
  profilePhoto: string | null;
  status: string;
};

export type AuthSession = {
  access_token: string;
  token_type: string;
  trainee: Trainee;
  // The company signed in to - set when the sign-in named none (the server found it).
  company?: Company | null;
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
  // From the master list; the zone starts the trainee's ID (e.g. SOUTH2610001).
  zone?: string;
  region?: string;
};

/** Self-registration (no password) also signs the new trainee in on this device - it returns their
 *  session. Registers into the phone's company (the QR's, or the code typed on the form). */
export function registerTrainee(payload: RegisterPayload) {
  return apiRequest<AuthSession>("/trainees/register", {
    method: "POST",
    body: JSON.stringify({ ...payload, phone: Number(payload.phone), deviceId: getDeviceId(), deviceName: getDeviceName() }),
  });
}

/** `identifier` is what the trainee typed: their username, HO ID, Trainee UID or phone. No company
 *  code - the server finds their company - and this device, which counts toward their device limit.
 *  `company`: signing in to join a training from its QR code, the company the QR names - an account
 *  of another company is refused with "No training access". */
export function loginTrainee(identifier: string, password: string, company?: string) {
  return apiRequest<AuthSession>(
    "/trainees/login",
    {
      method: "POST",
      body: JSON.stringify({ identifier, password, company, deviceId: getDeviceId(), deviceName: getDeviceName() }),
    },
    { company: false },
  );
}

/** Signs the trainee out on the server - on this device only. */
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

import { apiRequest, apiUpload } from "./client";

export type AttendanceRecord = {
  status: string;
  markedOn: string | null;
  distanceMeters: number | null;
};

export function checkIn(token: string, conferenceUid: string) {
  return apiRequest<AttendanceRecord>("/attendance/check-in", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ conferenceUid }),
  });
}

export type VerifyLocationResult = {
  distanceMeters: number | null;
  withinRadius: boolean | null;
  /** Geofence radius this check was made against, in metres (defaults to 100). */
  radiusMeters: number | null;
  venueLabel: string | null;
};

export function verifyLocation(token: string, conferenceUid: string, latitude: number, longitude: number) {
  return apiRequest<VerifyLocationResult>("/attendance/verify-location", {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
    body: JSON.stringify({ conferenceUid, latitude, longitude }),
  });
}

export type SecureCheckInPayload = {
  conferenceUid: string;
  latitude: number;
  longitude: number;
  photo: { uri: string; name: string; type: string };
};

export function secureCheckIn(token: string, payload: SecureCheckInPayload) {
  const formData = new FormData();
  formData.append("conferenceUid", payload.conferenceUid);
  formData.append("latitude", String(payload.latitude));
  formData.append("longitude", String(payload.longitude));
  formData.append("photo", {
    uri: payload.photo.uri,
    name: payload.photo.name,
    type: payload.photo.type,
  } as unknown as Blob);

  return apiUpload<AttendanceRecord>("/attendance/check-in/secure", formData, token);
}

export { ApiError } from "./client";

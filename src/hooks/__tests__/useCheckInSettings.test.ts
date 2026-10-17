import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";
import { Alert, AlertButton } from "react-native";

import { ApiError, fetchCheckInSettings, updateCheckInSettings } from "@/api/admin";
import { useCheckInSettings } from "@/hooks/useCheckInSettings";

jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminToken: "admin-token" }) }));
jest.mock("@/api/admin", () => {
  const { ApiError: RealApiError } = jest.requireActual<typeof import("@/api/client")>("@/api/client");
  return { ApiError: RealApiError, fetchCheckInSettings: jest.fn(), updateCheckInSettings: jest.fn() };
});

const mockFetch = jest.mocked(fetchCheckInSettings);
const mockUpdate = jest.mocked(updateCheckInSettings);

beforeEach(() => {
  jest.restoreAllMocks();
  mockFetch.mockReset();
  mockUpdate.mockReset();
});

async function renderAsSuperAdmin(faceDetectionEnabled = true) {
  mockFetch.mockResolvedValue({ faceDetectionEnabled });
  const { result } = await renderHook(() => useCheckInSettings());
  await waitFor(() => expect(result.current.settings).toEqual({ faceDetectionEnabled }));
  return result;
}

/** The buttons of the confirmation the last Alert showed. */
const lastAlertButtons = (alert: jest.Mock) => (alert.mock.calls.at(-1)?.[2] ?? []) as AlertButton[];

test("anyone but a Super Admin gets nothing to show", async () => {
  mockFetch.mockRejectedValue(new ApiError("This action requires a Super Admin account", 403));
  const { result } = await renderHook(() => useCheckInSettings());
  await waitFor(() => expect(mockFetch).toHaveBeenCalledWith("admin-token"));
  expect(result.current.settings).toBeNull();
});

test("turning it off asks first, and Cancel changes nothing", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  const result = await renderAsSuperAdmin(true);

  await act(() => result.current.setFaceDetection(false));
  expect(alert).toHaveBeenCalledTimes(1);
  expect(mockUpdate).not.toHaveBeenCalled();

  await act(() => lastAlertButtons(alert as jest.Mock).find((b) => b.style === "cancel")?.onPress?.());
  expect(mockUpdate).not.toHaveBeenCalled();
  expect(result.current.settings).toEqual({ faceDetectionEnabled: true });
});

test("confirming turns it off on the server", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  mockUpdate.mockResolvedValue({ faceDetectionEnabled: false });
  const result = await renderAsSuperAdmin(true);

  await act(() => result.current.setFaceDetection(false));
  await act(async () => lastAlertButtons(alert as jest.Mock).find((b) => b.style === "destructive")?.onPress?.());

  expect(mockUpdate).toHaveBeenCalledWith("admin-token", { faceDetectionEnabled: false });
  await waitFor(() => expect(result.current.settings).toEqual({ faceDetectionEnabled: false }));
});

test("turning it back on saves straight away; a failed save puts the switch back", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  mockUpdate.mockRejectedValue(new ApiError("Couldn't reach the server.", 0));
  const result = await renderAsSuperAdmin(false);

  await act(async () => result.current.setFaceDetection(true));

  expect(mockUpdate).toHaveBeenCalledWith("admin-token", { faceDetectionEnabled: true });
  await waitFor(() => expect(result.current.settings).toEqual({ faceDetectionEnabled: false }));
  expect(alert).toHaveBeenCalledWith("Couldn't save the setting", "Couldn't reach the server.");
  expect(result.current.saving).toBe(false);
});

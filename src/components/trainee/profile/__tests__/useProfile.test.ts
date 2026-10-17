import { expect, jest, test } from "@jest/globals";
import { renderHook } from "@testing-library/react-native";

import { placeName } from "@/components/trainee/profile/constants";
import { useProfile } from "@/components/trainee/profile/useProfile";

let mockTrainee: Record<string, unknown> | null = null;

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: jest.fn(), push: jest.fn(), replace: jest.fn() }),
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("expo-image-picker", () => ({}));
jest.mock("react-native-image-crop-picker", () => ({}));
jest.mock("@/api/auth", () => ({ ApiError: class extends Error {}, uploadTraineePhoto: jest.fn() }));
jest.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ trainee: mockTrainee, token: "trainee-token", logout: jest.fn(), setSession: jest.fn() }),
}));

const rows = (items: { label: string; value: string }[]) => Object.fromEntries(items.map((i) => [i.label, i.value]));

test("an empty profile shows -- everywhere, never a made-up value", async () => {
  mockTrainee = { name: "New Trainee", phone: 9876543210, email: "", status: "Active" };
  const { result } = await renderHook(() => useProfile());
  const shown = { ...rows(result.current.personalDetails), ...rows(result.current.organizationDetails) };

  expect(shown).toEqual({
    Mobile: "9876543210",
    Email: "--",
    Designation: "--",
    "Employee ID": "--",
    Zone: "--",
    Region: "--",
    "Reporting Manager": "--",
    "Manager's Designation": "--",
  });
  expect(JSON.stringify(shown)).not.toMatch(/anandkumar|ANAND ROY|SALES HEAD|8569741259|8750574444|SOUTH/);
  expect(result.current.sessionPillLabel).toBe("");
});

test("a filled profile shows the trainee's own values", async () => {
  mockTrainee = {
    phone: 9123450001, email: "a@example.test", designation: "Sales Executive", employee_id: "HO-1", zone: "North",
    region: "North 1", supervisorName: "R. Mehta", supervisorDesignation: "Store Manager", state: "up", district: "greater_noida",
  };
  const { result } = await renderHook(() => useProfile());

  expect(rows(result.current.personalDetails)).toMatchObject({ Zone: "North", Region: "North 1", Designation: "Sales Executive" });
  expect(rows(result.current.organizationDetails)).toEqual({ "Reporting Manager": "R. Mehta", "Manager's Designation": "Store Manager" });
  expect(result.current.sessionPillLabel).toBe("Greater Noida, UP");
});

test("a saved place name is kept; an old code reads as words", () => {
  expect(placeName("Haryana")).toBe("Haryana");
  expect(placeName("new_delhi")).toBe("New Delhi");
  expect(placeName("karnataka")).toBe("Karnataka");
  expect(placeName("up")).toBe("UP");
  expect(placeName(null)).toBe("");
});

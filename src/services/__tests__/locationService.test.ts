import { beforeEach, expect, jest, test } from "@jest/globals";
import * as Location from "expo-location";

import { getCurrentCoordinates } from "@/services/locationService";

jest.mock("expo-location", () => ({
  getLastKnownPositionAsync: jest.fn(),
  getCurrentPositionAsync: jest.fn(),
  Accuracy: { Balanced: 3 },
}));

const lastKnown = jest.mocked(Location.getLastKnownPositionAsync);
const current = jest.mocked(Location.getCurrentPositionAsync);

beforeEach(() => {
  lastKnown.mockReset();
  current.mockReset();
});

test("a recent last-known position is returned straight away", async () => {
  lastKnown.mockResolvedValue({ coords: { latitude: 28.61, longitude: 77.21, accuracy: 8 } } as never);
  await expect(getCurrentCoordinates()).resolves.toEqual({ latitude: 28.61, longitude: 77.21, accuracy: 8 });
});

test("with no real position at all it fails - never a made-up one", async () => {
  lastKnown.mockResolvedValue(null as never);
  current.mockRejectedValue(new Error("GPS off"));
  await expect(getCurrentCoordinates()).rejects.toThrow("LOCATION_UNAVAILABLE");
});

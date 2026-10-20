import { afterAll, beforeAll, expect, jest, test } from "@jest/globals";
import { render, screen } from "@testing-library/react-native";

import TrainerListFilterBar from "@/components/trainer/TrainerListFilterBar";
import { AdminFiltersProvider } from "@/hooks/useAdminFilters";

jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminToken: "trainer-token" }) }));
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));

beforeAll(() => {
  jest.useFakeTimers({ now: new Date("2026-10-15T06:00:00Z"), doNotFake: ["nextTick", "setImmediate"] });
});
afterAll(() => {
  jest.useRealTimers();
});

test("every trainer list opens on the 1st of this month to today, shown on the date filter", async () => {
  await render(
    <AdminFiltersProvider>
      <TrainerListFilterBar />
    </AdminFiltersProvider>,
  );
  expect(screen.getByLabelText("Select Range")).toBeTruthy();
  expect(screen.getByText("01 Oct 26 - 15 Oct 2026")).toBeTruthy();
}, 30_000);

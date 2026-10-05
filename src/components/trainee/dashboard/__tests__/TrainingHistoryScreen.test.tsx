import { beforeAll, beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react-native";

import { getTrainingHistory } from "@/api/session";
import TrainingHistoryScreen from "@/app/training_history";

// The route params the screen was opened with - a Dashboard metric card sets them.
let mockParams: { card?: string } = {};

jest.mock("expo-router", () => ({
  useRouter: () => ({ back: jest.fn(), push: jest.fn(), replace: jest.fn() }),
  useLocalSearchParams: () => mockParams,
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ token: "trainee-token" }) }));
jest.mock("@/api/session", () => ({ getTrainingHistory: jest.fn() }));

const mockHistory = jest.mocked(getTrainingHistory);

beforeEach(() => {
  mockParams = {};
  mockHistory.mockReset();
  mockHistory.mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 20, totalPages: 0 });
});

// The first render loads the icon set and components from scratch; do it once here, so each test
// below runs within the normal per-test limit.
beforeAll(async () => {
  mockHistory.mockResolvedValue({ items: [], total: 0, page: 1, pageSize: 20, totalPages: 0 });
  await render(<TrainingHistoryScreen />);
}, 30_000);

test("the filter button opens and closes the filter panel", async () => {
  await render(<TrainingHistoryScreen />);
  expect(screen.queryByText("Date Range")).toBeNull(); // closed to start with

  await fireEvent.press(screen.getByLabelText("Show filters"));
  expect(screen.getByText("Date Range")).toBeTruthy();

  await fireEvent.press(screen.getByLabelText("Hide filters"));
  expect(screen.queryByText("Date Range")).toBeNull();
});

test("closed with a filter still applied, the filter button carries a dot", async () => {
  mockParams = { card: "present" };
  await render(<TrainingHistoryScreen />);
  expect(screen.getByText("Date Range")).toBeTruthy(); // opened from a card: starts open
  expect(screen.queryByTestId("filters-applied-dot")).toBeNull();

  await fireEvent.press(screen.getByLabelText("Hide filters"));
  expect(screen.getByTestId("filters-applied-dot")).toBeTruthy();
});

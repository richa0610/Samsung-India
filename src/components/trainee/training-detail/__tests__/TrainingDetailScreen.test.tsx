import { beforeAll, expect, jest, test } from "@jest/globals";
import { render, screen } from "@testing-library/react-native";

import TrainingDetailScreen from "@/app/training_detail";

// What the screen's data hook returns - each test sets the training it shows.
const mockHook = {
  onBack: jest.fn(),
  detail: null as unknown,
  loading: false,
  error: null,
  reload: jest.fn(),
  expandedKeys: new Set<string>(),
  toggleModule: jest.fn(),
};
jest.mock("@/hooks/useTrainingDetail", () => ({ useTrainingDetail: () => mockHook }));
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));

const training = (status: string) => ({
  conferenceUid: "CONF-1",
  title: "Galaxy Basics",
  date: "2026-10-03",
  location: null,
  trainerName: "Asha",
  status,
  modules: [{ key: "STANDARD_TEST", name: "Post Test", status: "Completed", score: "2/3", completedAt: null, questions: [] }],
});

// The first render loads the icon set and components from scratch; do it once here, so each test
// below runs within the normal per-test limit.
beforeAll(async () => {
  mockHook.detail = training("Completed");
  await render(<TrainingDetailScreen />);
}, 30_000);

test("an ongoing training asks the trainee to wait until it's completed", async () => {
  mockHook.detail = training("Ongoing");
  await render(<TrainingDetailScreen />);

  expect(screen.getByText("Training In Progress")).toBeTruthy();
  expect(screen.getByText(/full details will be available here once it's completed/)).toBeTruthy();
  expect(screen.queryByText("Post Test")).toBeNull(); // no module breakdown yet
});

test("a completed training shows its module breakdown", async () => {
  mockHook.detail = training("Completed");
  await render(<TrainingDetailScreen />);

  expect(screen.getByText("Post Test")).toBeTruthy();
  expect(screen.queryByText("Training In Progress")).toBeNull();
});

test("a missed training still shows the missed notice", async () => {
  mockHook.detail = training("Missed");
  await render(<TrainingDetailScreen />);

  expect(screen.getByText("Session Missed")).toBeTruthy();
  expect(screen.queryByText("Post Test")).toBeNull();
});

import { beforeAll, beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react-native";

import AdminBottomNav from "../AdminBottomNav";

const mockPush = jest.fn();
let mockPathname = "/admin_training_list";

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
  usePathname: () => mockPathname,
}));
jest.mock("react-native-safe-area-context", () => ({
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));

// The first render loads the icon set and components from scratch (~7 s on a cold cache); do it
// once here, so each test below runs within the normal per-test limit.
beforeAll(async () => {
  await render(<AdminBottomNav activeTab="home" onSelectTab={jest.fn()} />);
}, 30_000);

beforeEach(() => {
  mockPush.mockReset();
});

async function choose(tab: string, item: string) {
  await fireEvent.press(screen.getByText(tab));
  await fireEvent.press(screen.getByText(item));
}

test("choosing the page you are already on does not open it again", async () => {
  mockPathname = "/admin_training_list";
  await render(<AdminBottomNav activeTab="training" onSelectTab={jest.fn()} />);

  await choose("Training", "Training List");
  expect(mockPush).not.toHaveBeenCalled();
});

test("other pages still open", async () => {
  mockPathname = "/admin_training_list";
  await render(<AdminBottomNav activeTab="training" onSelectTab={jest.fn()} />);

  await choose("Training", "Pending Training");
  expect(mockPush).toHaveBeenCalledWith("/admin_pending_trainings");
});

test("the attendance menu follows the same rule", async () => {
  mockPathname = "/admin_attendance_list";
  await render(<AdminBottomNav activeTab="attendance" onSelectTab={jest.fn()} />);

  await choose("Attendance", "Attendance List");
  expect(mockPush).not.toHaveBeenCalled();
});

test("another attendance page still opens", async () => {
  mockPathname = "/admin_attendance_list";
  await render(<AdminBottomNav activeTab="attendance" onSelectTab={jest.fn()} />);

  await choose("Attendance", "Confirmed Attendance");
  expect(mockPush).toHaveBeenCalledWith("/admin_confirmed_attendance");
});

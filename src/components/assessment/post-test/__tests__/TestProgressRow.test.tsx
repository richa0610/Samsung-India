import { afterEach, expect, jest, test } from "@jest/globals";
import { render, screen } from "@testing-library/react-native";

import TestProgressRow from "@/components/assessment/post-test/TestProgressRow";
import { setProctoringSettings } from "@/components/proctoring/violations";

jest.mock("@/components/proctoring/OnDeviceProctoringPanel", () => {
  const { View } = require("react-native");
  return function MockProctoringPanel() {
    return <View testID="mock-proctoring-camera" />;
  };
});
jest.mock("@/components/ui/TimeProgress", () => {
  const { View } = require("react-native");
  return function MockTimeProgress() {
    return <View testID="mock-timer" />;
  };
});

const row = (
  <TestProgressRow
    totalMinutes={15}
    remainingMinutes={14}
    remainingSecondsPart={45}
    token="token"
    isActive
    paused={false}
    violationCount={0}
    currentViolation={null}
    onViolation={jest.fn()}
    onWarning={jest.fn()}
  />
);

afterEach(() => setProctoringSettings(true, 3));

test("with proctoring on for the company, the timer and the proctoring camera show", async () => {
  setProctoringSettings(true, 3);
  await render(row);
  expect(screen.getByTestId("mock-timer")).toBeTruthy();
  expect(screen.getByTestId("mock-proctoring-camera")).toBeTruthy();
});

test("with proctoring off for the company, only the timer shows - no camera", async () => {
  setProctoringSettings(false, 3);
  await render(row);
  expect(screen.getByTestId("mock-timer")).toBeTruthy();
  expect(screen.queryByTestId("mock-proctoring-camera")).toBeNull();
});

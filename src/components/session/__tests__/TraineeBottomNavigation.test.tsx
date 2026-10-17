import React from "react";
import { beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react-native";

import TraineeBottomNavigation from "../TraineeBottomNavigation";

jest.mock("react-native-safe-area-context", () => ({
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));

jest.mock("@/assets/images/svg/home.svg", () => {
  const { View } = require("react-native");
  return function MockHomeIcon(props: any) {
    return <View {...props} testID="mock-home-icon" />;
  };
});

test("when training is not live, Rank tab is hidden", async () => {
  const onSelectTab = jest.fn();
  await render(
    <TraineeBottomNavigation
      activeTab="home"
      onSelectTab={onSelectTab}
      isTrainingLive={false}
    />,
  );

  expect(screen.queryByText("Rank")).toBeNull();
  expect(screen.getByText("Dashboard")).toBeTruthy();
  expect(screen.getByText("Home")).toBeTruthy();
  expect(screen.getByText("Profile")).toBeTruthy();
});

test("by default (no isTrainingLive prop passed), Rank tab is hidden", async () => {
  const onSelectTab = jest.fn();
  await render(
    <TraineeBottomNavigation
      activeTab="home"
      onSelectTab={onSelectTab}
    />,
  );

  expect(screen.queryByText("Rank")).toBeNull();
  expect(screen.getByText("Dashboard")).toBeTruthy();
  expect(screen.getByText("Home")).toBeTruthy();
  expect(screen.getByText("Profile")).toBeTruthy();
});

test("when training is live, Rank tab is visible and clickable", async () => {
  const onSelectTab = jest.fn();
  await render(
    <TraineeBottomNavigation
      activeTab="home"
      onSelectTab={onSelectTab}
      isTrainingLive={true}
    />,
  );

  expect(screen.getByText("Rank")).toBeTruthy();
  expect(screen.getByText("Dashboard")).toBeTruthy();
  expect(screen.getByText("Home")).toBeTruthy();
  expect(screen.getByText("Profile")).toBeTruthy();

  fireEvent.press(screen.getByText("Rank"));
  expect(onSelectTab).toHaveBeenCalledWith("rank");
});

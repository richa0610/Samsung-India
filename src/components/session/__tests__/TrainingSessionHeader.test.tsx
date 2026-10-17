import React from "react";
import { expect, jest, test } from "@jest/globals";
import { render, screen } from "@testing-library/react-native";

import TrainingSessionHeader from "../TrainingSessionHeader";

jest.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ token: "test-token" }),
}));

jest.mock("@/assets/images/svg/calender2.svg", () => {
  const { View } = require("react-native");
  return function MockCalendarIcon(props: any) {
    return <View {...props} testID="mock-calendar-icon" />;
  };
});

test("when showSessionDetails is false, session title, pill, and meta row are not rendered", async () => {
  await render(
    <TrainingSessionHeader
      userName="Anjali Verma"
      showSessionDetails={false}
      title="Training Session"
      sessionType="Training"
      date="16 Oct 2026"
      location="Delhi"
      confirmationStatus="Not Confirmed"
      userSubtitle="Sales Executive"
    />,
  );

  expect(screen.getByText("Anjali Verma")).toBeTruthy();
  expect(screen.getByText("Sales Executive")).toBeTruthy();
  expect(screen.queryByText("Training Session")).toBeNull();
  expect(screen.queryByText("TRAINING")).toBeNull();
  expect(screen.queryByText("16 Oct 2026")).toBeNull();
  expect(screen.queryByText("Delhi")).toBeNull();
  expect(screen.queryByText("Not Confirmed")).toBeNull();
});

test("when showSessionDetails is true, session title, pill, meta row, and status are rendered", async () => {
  await render(
    <TrainingSessionHeader
      userName="Anjali Verma"
      showSessionDetails={true}
      title="Galaxy AI Workshop"
      sessionType="Workshop"
      date="16 Oct 2026"
      location="Mumbai"
      confirmationStatus="Confirmed"
    />,
  );

  expect(screen.getByText("Anjali Verma")).toBeTruthy();
  expect(screen.getByText("Galaxy AI Workshop")).toBeTruthy();
  expect(screen.getByText("Workshop")).toBeTruthy();
  expect(screen.getByText("16 Oct 2026")).toBeTruthy();
  expect(screen.getByText("Mumbai")).toBeTruthy();
  expect(screen.getByText("Confirmed")).toBeTruthy();
  expect(screen.getAllByTestId("mock-calendar-icon")).toHaveLength(2);
});

test("when isTrainingLive is false, calendar and location meta row are not rendered", async () => {
  await render(
    <TrainingSessionHeader
      userName="Anjali Verma"
      showSessionDetails={true}
      isTrainingLive={false}
      title="Training Session"
      sessionType="Training"
      date="16 Oct 2026"
      location="Delhi"
      confirmationStatus="Not Confirmed"
    />,
  );

  expect(screen.getByText("Anjali Verma")).toBeTruthy();
  expect(screen.getByText("Training Session")).toBeTruthy();
  expect(screen.queryByText("16 Oct 2026")).toBeNull();
  expect(screen.queryByText("Delhi")).toBeNull();
  // Only the session pill calendar icon is rendered, not the meta row one
  expect(screen.getAllByTestId("mock-calendar-icon")).toHaveLength(1);
});

test("when date and location are '--' or empty, calendar and location meta row are not rendered", async () => {
  await render(
    <TrainingSessionHeader
      userName="Anjali Verma"
      showSessionDetails={true}
      title="Training Session"
      sessionType="Training"
      date="--"
      location="--"
      confirmationStatus="Not Confirmed"
    />,
  );

  expect(screen.getByText("Anjali Verma")).toBeTruthy();
  expect(screen.getByText("Training Session")).toBeTruthy();
  expect(screen.queryByText("--")).toBeNull();
  // Only the session pill calendar icon is rendered, not the meta row one
  expect(screen.getAllByTestId("mock-calendar-icon")).toHaveLength(1);
});

test("when showSessionPill is false, title is rendered without session pill", async () => {
  await render(
    <TrainingSessionHeader
      userName="Anjali Verma"
      showSessionDetails={true}
      showSessionPill={false}
      title="Trainings"
      userSubtitle="Sales Associate"
    />,
  );

  expect(screen.getByText("Anjali Verma")).toBeTruthy();
  expect(screen.getByText("Sales Associate")).toBeTruthy();
  expect(screen.getByText("Trainings")).toBeTruthy();
  expect(screen.queryByTestId("mock-calendar-icon")).toBeNull();
});

test("renders Trainings badge in white pill when sessionType is Trainings", async () => {
  await render(
    <TrainingSessionHeader
      userName="Anjali Verma"
      showSessionDetails={true}
      showSessionPill={true}
      sessionType="Trainings"
      userSubtitle="Sales Associate"
    />,
  );

  expect(screen.getByText("Anjali Verma")).toBeTruthy();
  expect(screen.getByText("Sales Associate")).toBeTruthy();
  expect(screen.getByText("Trainings")).toBeTruthy();
  expect(screen.getAllByTestId("mock-calendar-icon")).toHaveLength(1);
});

import { expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react-native";
import React from "react";

import StatusNoticeCard from "../StatusNoticeCard";

test("renders missed session card with details and back button", async () => {
  const onBack = jest.fn();
  await render(
    <StatusNoticeCard
      status="Missed"
      title="Session Missed"
      message="You missed this training. Try to join your next scheduled session on time."
      sessionTitle="Classroom Training"
      date="2026-10-06"
      location="dibrugarh, Assam"
      trainerName="Rahul Sharma"
      onBack={onBack}
    />,
  );

  expect(screen.getByText("MISSED SESSION")).toBeTruthy();
  expect(screen.getByText("Session Missed")).toBeTruthy();
  expect(screen.getByText(/You missed this training/)).toBeTruthy();
  expect(screen.getByText("Session Details")).toBeTruthy();
  expect(screen.getByText("Classroom Training")).toBeTruthy();
  expect(screen.getByText("dibrugarh, Assam")).toBeTruthy();
  expect(screen.getByText("Rahul Sharma")).toBeTruthy();
  expect(screen.getByText("Important Note")).toBeTruthy();

  const button = screen.getByText("Back to Trainings");
  expect(button).toBeTruthy();
  fireEvent.press(button);
  expect(onBack).toHaveBeenCalledTimes(1);
});

test("renders marked absent status and text", async () => {
  await render(
    <StatusNoticeCard
      status="Absent"
      title="Marked Absent"
      message="You were marked absent for this training."
      sessionTitle="Classroom Training"
      onBack={jest.fn()}
    />,
  );

  expect(screen.getByText("MARKED ABSENT")).toBeTruthy();
  expect(screen.getByText("Marked Absent")).toBeTruthy();
  expect(screen.getByText("You were marked absent for this training.")).toBeTruthy();
});

test("triggers onGoDashboard when View Dashboard is pressed", async () => {
  const onGoDashboard = jest.fn();
  await render(
    <StatusNoticeCard
      status="Absent"
      title="Marked Absent"
      message="You were marked absent for this training."
      onBack={jest.fn()}
      onGoDashboard={onGoDashboard}
    />,
  );

  const dashBtn = screen.getByText("View Dashboard");
  expect(dashBtn).toBeTruthy();
  fireEvent.press(dashBtn);
  expect(onGoDashboard).toHaveBeenCalledTimes(1);
});

test("renders retest items for missed session and triggers onRetest", async () => {
  const onRetest = jest.fn();
  await render(
    <StatusNoticeCard
      status="Missed"
      title="Session Missed"
      message="You missed this training."
      onBack={jest.fn()}
      retestItems={[
        { key: "STANDARD_TEST", name: "Standard Test", suiteUid: "SUITE-1", done: false, score: null },
        { key: "SURVEY", name: "Survey Module", suiteUid: "SURVEY-1", done: true, score: null },
      ]}
      onRetest={onRetest}
    />,
  );

  expect(screen.getByText("Retest & Survey Retake")).toBeTruthy();
  expect(screen.getByText("Standard Test")).toBeTruthy();
  expect(screen.getByText("Survey Module")).toBeTruthy();
  expect(screen.getByText("Completed")).toBeTruthy();

  const startRetestBtn = screen.getByText("Start Retest");
  expect(startRetestBtn).toBeTruthy();
  fireEvent.press(startRetestBtn);
  expect(onRetest).toHaveBeenCalledWith("STANDARD_TEST", "SUITE-1");
});

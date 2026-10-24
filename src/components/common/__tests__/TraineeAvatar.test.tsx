import React from "react";
import { expect, jest, test } from "@jest/globals";
import { render, screen } from "@testing-library/react-native";

import TraineeAvatar from "../TraineeAvatar";

jest.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({ token: "test-token" }),
}));

const STYLE = { width: 60, height: 60, borderRadius: 30 };

test("no photo and no known gender shows the trainee's initials", async () => {
  await render(<TraineeAvatar person={{ name: "Pooja Sharma", gender: null, profilePhoto: null }} style={STYLE} />);

  expect(screen.getByTestId("trainee-avatar-initials")).toBeTruthy();
  expect(screen.getByText("PS")).toBeTruthy();
});

test("a known gender, however it was typed, shows its picture rather than initials", async () => {
  await render(<TraineeAvatar person={{ name: "Pooja Sharma", gender: " f ", profilePhoto: null }} style={STYLE} />);

  expect(screen.queryByTestId("trainee-avatar-initials")).toBeNull();
  expect(screen.queryByText("PS")).toBeNull();
});

test("no name, photo or gender still shows a round placeholder, without letters", async () => {
  await render(<TraineeAvatar person={null} style={STYLE} />);

  expect(screen.getByTestId("trainee-avatar-initials")).toBeTruthy();
});

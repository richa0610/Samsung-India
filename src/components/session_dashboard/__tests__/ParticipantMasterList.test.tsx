import { expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react-native";
import { Alert, StyleSheet } from "react-native";

import type { TraineeRow } from "@/api/training";
import { participantsFromTrainees } from "../dashboard-screen/participantMapper";
import ParticipantAttendanceCard from "../ParticipantAttendanceCard";
import { PARTICIPANT_COLUMNS, PARTICIPANT_TABLE_MIN_WIDTH, columnWidths } from "../participantColumns";

jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));

const row = (overrides: Partial<TraineeRow>): TraineeRow => ({
  traineeUid: "TR-1",
  name: "Sumit",
  employeeId: "YAT002",
  phone: 9315513673,
  audienceType: "UNASSIGNED",
  status: "Present",
  markedOn: null,
  checkOutTime: null,
  score: null,
  profilePhoto: null,
  isLocked: false,
  proctoringStrikes: 0,
  proctoringMaxStrikes: 3,
  proctoringLogs: [],
  ...overrides,
});

test("each participant shows their attendance stage and a done / not done chip per activity", async () => {
  const participants = participantsFromTrainees([
    row({
      stage: "Attendance",
      stageModules: [
        { key: "STANDARD_TEST", label: "Test", done: true },
        { key: "SURVEY", label: "Survey", done: false },
      ],
    }),
  ]);

  await render(<ParticipantAttendanceCard participants={participants} />);

  expect(screen.getByText("STAGE")).toBeTruthy();
  expect(screen.getByText("Attendance")).toBeTruthy();
  expect(screen.getByLabelText("Test: done")).toBeTruthy();
  expect(screen.getByLabelText("Survey: not done")).toBeTruthy();
});

test("a row from a server without the stage yet reads Not Started, with no chips", () => {
  const [participant] = participantsFromTrainees([row({})]);
  expect(participant.stage).toBe("Not Started");
  expect(participant.stageModules).toEqual([]);
});

test("the status reads P, A or NM - and a screen reader hears the full word", async () => {
  const participants = participantsFromTrainees([
    row({ traineeUid: "PRESENT", status: "Present" }),
    row({ traineeUid: "ABSENT", status: "Absent" }),
    row({ traineeUid: "JOINED", status: "Pending" }),
  ]);

  await render(<ParticipantAttendanceCard participants={participants} />);

  expect(screen.getByLabelText("Present")).toHaveTextContent("P");
  expect(screen.getByLabelText("Absent")).toHaveTextContent("A");
  expect(screen.getByLabelText("Not marked")).toHaveTextContent("NM");
});

test("only Present and Absent count as marked - joined or test-only trainees are NM", () => {
  const statuses = participantsFromTrainees(
    ["Present", "Absent", "Pending", "Attempted", "present", "ABSENT"].map((status, i) => row({ traineeUid: `T${i}`, status })),
  ).map((p) => p.status);
  expect(statuses).toEqual(["PRESENT", "ABSENT", "NOT_MARKED", "NOT_MARKED", "PRESENT", "ABSENT"]);
});

test("there's no audience column - the audience type is a short tag after the phone number", async () => {
  const participants = participantsFromTrainees([
    row({ traineeUid: "ROSTER", audienceType: "ASSIGNED" }),
    row({ traineeUid: "JOINED", audienceType: "UNASSIGNED" }),
    row({ traineeUid: "NEW", audienceType: "FRESH" }),
  ]);

  await render(<ParticipantAttendanceCard participants={participants} />);

  expect(screen.queryByText(/AUDIENCE/)).toBeNull();
  expect(screen.getByLabelText("Audience: Assigned")).toHaveTextContent("ASN");
  expect(screen.getByLabelText("Audience: Unassigned")).toHaveTextContent("UASN");
  expect(screen.getByLabelText("Audience: Fresh")).toHaveTextContent("FRESH");
});

test("an older server's NOT ALLOCATED, or anything unknown, reads as unassigned", () => {
  const types = participantsFromTrainees(
    ["ASSIGNED", "FRESH", "UNASSIGNED", "NOT ALLOCATED", ""].map((audienceType, i) => row({ traineeUid: `T${i}`, audienceType })),
  ).map((p) => p.attendeeType);
  expect(types).toEqual(["ASSIGNED", "FRESH", "UNASSIGNED", "UNASSIGNED", "UNASSIGNED"]);
});

test("the Score column shows each score green when it passes, red when it doesn't, and - without one", async () => {
  const participants = participantsFromTrainees([
    row({ traineeUid: "PASSED", score: "95%", scorePassed: true }),
    row({ traineeUid: "FAILED", score: "30%", scorePassed: false }),
    row({ traineeUid: "NOT_YET", score: null, scorePassed: null }),
  ]);

  await render(<ParticipantAttendanceCard participants={participants} />);

  expect(screen.getByText("SCORE")).toBeTruthy();
  expect(screen.getByLabelText("Score 95%, passed")).toHaveTextContent("95%");
  expect(screen.getByLabelText("Score 30%, below the pass mark")).toHaveTextContent("30%");
  expect(screen.getByLabelText("No score yet")).toHaveTextContent("-");
});

test("the table scrolls sideways, header and rows together, never narrower than its columns", async () => {
  await render(<ParticipantAttendanceCard participants={participantsFromTrainees([row({})])} />);

  const table = screen.getByHintText("Scroll sideways to see every column");
  expect(table.props.horizontal).toBe(true);
  // The header and the row are both inside it.
  expect(screen.getByText("SCORE")).toBeTruthy();
  expect(screen.getByText("Sumit")).toBeTruthy();
  expect(PARTICIPANT_TABLE_MIN_WIDTH).toBeGreaterThan(400); // wider than a phone's card, hence the scroll
});

test("with no one joined, the message sits outside the sideways scroll", async () => {
  await render(<ParticipantAttendanceCard participants={[]} />);
  expect(screen.getByText("No one has joined yet.")).toBeTruthy();
});

test("every column has one fixed width: the base width on a phone, all stretched alike on a wide screen", () => {
  // A phone's card is narrower than the table: base widths, and the table scrolls.
  expect(columnWidths(330)).toEqual(PARTICIPANT_COLUMNS);
  expect(columnWidths(0)).toEqual(PARTICIPANT_COLUMNS); // before the card has measured itself

  // A tablet's card is wider: every column grows by the same factor and the row still fits.
  const wide = columnWidths(900);
  const total = Object.values(wide).reduce((sum, width) => sum + width, 0);
  expect(total).toBeLessThanOrEqual(900);
  expect(total).toBeGreaterThan(900 - PARTICIPANT_TABLE_MIN_WIDTH * 0.05);
  for (const [column, width] of Object.entries(wide)) {
    expect(width / PARTICIPANT_COLUMNS[column as keyof typeof PARTICIPANT_COLUMNS]).toBeCloseTo(900 / PARTICIPANT_TABLE_MIN_WIDTH, 1);
  }
});

test("the Participant Details column is left-aligned and stays frozen while the table scrolls sideways", async () => {
  await render(<ParticipantAttendanceCard participants={participantsFromTrainees([row({})])} />);

  // The table follows its own sideways scroll, which the frozen column is shifted by.
  const table = screen.getByHintText("Scroll sideways to see every column");
  expect(table.props.onScroll).toBeDefined();
  expect(table.props.scrollEventThrottle).toBe(16);

  // Heading and values read from the left.
  expect(StyleSheet.flatten(screen.getByText("PARTICIPANT\nDETAILS").props.style).textAlign).toBe("left");
  expect(StyleSheet.flatten(screen.getByText("Sumit").props.style).textAlign).toBe("left");
  expect(StyleSheet.flatten(screen.getByText("STAGE").props.style).textAlign).toBe("center");
});

const locked = (unlocksUsed: number) =>
  participantsFromTrainees([
    row({ isLocked: true, proctoringStrikes: 3, proctoringUnlocks: unlocksUsed, proctoringMaxUnlocks: 2 }),
  ]);

test("beside the controls each trainee shows how many times the trainer unlocked them - locked now or not", async () => {
  await render(
    <ParticipantAttendanceCard
      participants={participantsFromTrainees([
        row({ traineeUid: "TR-1", name: "Sumit", proctoringUnlocks: 1, proctoringMaxUnlocks: 2 }),
        row({ traineeUid: "TR-2", name: "Asha", isLocked: true, proctoringStrikes: 3, proctoringUnlocks: 2, proctoringMaxUnlocks: 2 }),
        row({ traineeUid: "TR-3", name: "Ravi" }),
      ])}
      canEdit
    />,
  );
  expect(screen.getByLabelText("Unlocked 1 of 2 times")).toBeTruthy();
  expect(screen.getByLabelText("Unlocked 2 of 2 times")).toBeTruthy();
  expect(screen.getAllByLabelText(/^Unlocked \d of \d times$/)).toHaveLength(2);   // never unlocked: nothing shown
});

test("with an unlock left, the unlock form says only 2 are allowed and which one this is", async () => {
  await render(<ParticipantAttendanceCard participants={locked(1)} canEdit />);

  await fireEvent.press(screen.getByLabelText("Unlock Sumit, 1 of 2 unlocks used"));

  expect(screen.getByText(/UNLOCK EXAM FOR/)).toBeTruthy();
  expect(screen.getByText(/Only 2 unlocks are allowed per trainee in a training/)).toBeTruthy();
  expect(screen.getByText(/This is unlock 2 of 2 - after this, they can't be unlocked again/)).toBeTruthy();
});

test("with both unlocks used, tapping unlock shows the limit popup instead of the form", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  await render(<ParticipantAttendanceCard participants={locked(2)} canEdit />);

  await fireEvent.press(screen.getByLabelText("Unlock Sumit: no unlocks left"));

  expect(alert).toHaveBeenCalledWith("Unlock limit reached", expect.stringContaining("already been unlocked 2 times"));
  expect(screen.queryByText(/UNLOCK EXAM FOR/)).toBeNull();
  alert.mockRestore();
});

import { beforeAll, expect, test } from "@jest/globals";
import { render, screen, within } from "@testing-library/react-native";

import TrainingDetailsTable, { TrainingRowData, ordinal } from "../TrainingDetailsTable";

const row = (n: number): TrainingRowData => ({
  id: `CONF-${n}`,
  trainingName: `Training ${n}`,
  status: "Completed",
  date: "03 Oct 2026",
  day: "(Sat)",
  postTestScore: "-",
  quizScore: "-",
  ranking: "-",
});

// The first render loads the icon set and components from scratch; do it once here, so each test
// below runs within the normal per-test limit.
beforeAll(async () => {
  await render(<TrainingDetailsTable trainings={[]} />);
}, 30_000);

test("the first column is S.No, numbering the rows in the order shown", async () => {
  await render(<TrainingDetailsTable trainings={[row(7), row(4), row(9)]} onPressRow={() => {}} />);

  expect(screen.getByText("S.No")).toBeTruthy();
  ["Training 7", "Training 4", "Training 9"].forEach((name, index) => {
    const tableRow = screen.getByLabelText(`View details for ${name}`);
    expect(within(tableRow).getByText(String(index + 1))).toBeTruthy();
  });
});

test("the restyled row still shows every value as given", async () => {
  const scored: TrainingRowData = {
    ...row(1),
    status: "Ongoing",
    postTestScore: "7/10",
    quizScore: "2/5",
    ranking: "3",
    rankingScope: "Session",
  };
  await render(<TrainingDetailsTable trainings={[scored]} onPressRow={() => {}} />);
  const tableRow = within(screen.getByLabelText("View details for Training 1"));

  expect(tableRow.getByText("Ongoing")).toBeTruthy();
  expect(tableRow.getByText("03 Oct 2026")).toBeTruthy();
  expect(tableRow.getByText("(Sat)")).toBeTruthy();
  expect(tableRow.getByText("7")).toBeTruthy();
  expect(tableRow.getByText("/10")).toBeTruthy();
  expect(tableRow.getByText("2")).toBeTruthy();
  expect(tableRow.getByText("/5")).toBeTruthy();
  expect(tableRow.getByText("3rd")).toBeTruthy();
  expect(screen.getByText("(Session)")).toBeTruthy(); // the scope is said once, in the column header
  expect(tableRow.queryByText("Session")).toBeNull();
});

test("ranks read as ordinals", () => {
  const cases: [string, string][] = [
    ["1", "1st"], ["2", "2nd"], ["3", "3rd"], ["4", "4th"], ["11", "11th"], ["12", "12th"],
    ["13", "13th"], ["21", "21st"], ["22", "22nd"], ["101", "101st"], ["111", "111th"], ["N/A", "N/A"],
  ];
  for (const [rank, shown] of cases) expect(ordinal(rank)).toBe(shown);
});

test("a rank in another scope still names it on the row", async () => {
  await render(<TrainingDetailsTable trainings={[{ ...row(1), ranking: "1", rankingScope: "State" }]} onPressRow={() => {}} />);
  const tableRow = within(screen.getByLabelText("View details for Training 1"));
  expect(tableRow.getByText("1st")).toBeTruthy();
  expect(tableRow.getByText("State")).toBeTruthy();
});

test("with no trainings it says so", async () => {
  await render(<TrainingDetailsTable trainings={[]} />);
  expect(screen.getByText("No trainings yet")).toBeTruthy();
  expect(screen.getByText("0")).toBeTruthy(); // the count pill (no View All on the full history)
});

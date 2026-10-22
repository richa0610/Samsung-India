import { expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen } from "@testing-library/react-native";

import LiveStudioQuestionRow from "@/components/session_dashboard/LiveStudioQuestionRow";

const question = (extra: { isActive?: boolean; wasBroadcast?: boolean }) => ({
  id: 7, qNumber: "Q1", timerSecs: 30, questionText: "Which band?", points: 15, responseCount: 1,
  isActive: false, ...extra,
});

test("a question not yet sent offers Broadcast", async () => {
  const onBroadcast = jest.fn();
  await render(<LiveStudioQuestionRow question={question({})} onBroadcast={onBroadcast} />);
  await fireEvent.press(screen.getByText("Broadcast"));
  expect(onBroadcast).toHaveBeenCalledWith(7);
});

test("the live question shows Live", async () => {
  await render(<LiveStudioQuestionRow question={question({ isActive: true })} onBroadcast={jest.fn()} />);
  expect(screen.getByText("Live")).toBeTruthy();
});

test("a question that already went live is marked Broadcasted and can't be sent again", async () => {
  const onBroadcast = jest.fn();
  await render(<LiveStudioQuestionRow question={question({ wasBroadcast: true })} onBroadcast={onBroadcast} />);
  expect(screen.queryByText("Broadcast")).toBeNull();
  await fireEvent.press(screen.getByText("Broadcasted"));
  expect(onBroadcast).not.toHaveBeenCalled();
});

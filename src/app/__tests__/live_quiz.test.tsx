import { beforeEach, expect, jest, test } from "@jest/globals";
import { render, screen } from "@testing-library/react-native";

import LiveQuizScreen from "@/app/live_quiz";
import { useLiveQuiz } from "@/hooks/useLiveQuiz";

jest.mock("expo-router", () => ({ useFocusEffect: jest.fn() }));
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ trainee: { traineeUid: "TRN-1" } }) }));
jest.mock("@/hooks/useLiveQuiz", () => ({ useLiveQuiz: jest.fn() }));
jest.mock("@/hooks/useLiveQuizSummary", () => ({
  useLiveQuizSummary: () => ({
    summary: null, recapIndex: null, openRecap: jest.fn(), openReview: jest.fn(), closeRecap: jest.fn(), stepRecap: jest.fn(),
  }),
}));
jest.mock("@/api/session", () => ({ isModuleLeft: () => false, markModuleLeft: jest.fn(), submitLiveQuiz: jest.fn() }));
jest.mock("@/components/quiz", () => ({
  QuizLiveHeader: () => null,
  QuizWaiting: jest.requireActual<{ default: unknown }>("@/components/quiz/QuizWaiting").default,
}));
jest.mock("@/components/quiz/assessment-map", () => ({ AssessmentMap: () => null, QuestionRecapSheet: () => null }));
jest.mock("@/components/quiz/LiveQuizQuestionView", () => () => null);
jest.mock("@/assets/images/svg/bell.svg", () => () => null);
jest.mock("@/assets/images/svg/clock.svg", () => () => null);
jest.mock("@/assets/images/svg/eye.svg", () => () => null);
jest.mock("@/assets/images/svg/people.svg", () => () => null);
jest.mock("@/assets/images/svg/Refresh cw.svg", () => () => null);

const mockUseLiveQuiz = jest.mocked(useLiveQuiz);
const QUESTION = { id: 12, text: "Which band?", options: [], order: 2, total: 5 };

function quizState(feedback: object | null) {
  return {
    view: { state: "QUESTION_LIVE", question: QUESTION },
    phase: feedback ? "feedback" : "waiting",
    feedback,
    loadError: null,
    selectedOption: null,
    secondsLeft: 0,
    timerPaused: false,
    submitting: false,
    connected: true,
    conferenceUid: "CONF-1",
    token: "token",
    selectOption: jest.fn(),
    onFinalSubmit: jest.fn(),
    refetch: jest.fn(),
    router: { replace: jest.fn() },
  } as unknown as ReturnType<typeof useLiveQuiz>;
}

const answered = (kind: "correct" | "incorrect" | "timeout") => ({
  kind, question: QUESTION, selectedOptionId: "B", correctOptionId: "A", explanation: "Because.",
});

beforeEach(() => {
  mockUseLiveQuiz.mockReset();
});

test("after answering, the trainee waits for the trainer's next question - no result card", async () => {
  for (const kind of ["correct", "incorrect"] as const) {
    mockUseLiveQuiz.mockReturnValue(quizState(answered(kind)));
    const { unmount } = await render(<LiveQuizScreen />);
    expect(screen.getByText("Trainer...")).toBeTruthy();
    expect(screen.getByText(/Your answer is saved\./)).toBeTruthy();
    expect(screen.getByText("Question 3 starting soon")).toBeTruthy();
    expect(screen.queryByText("Because.")).toBeNull();   // the explanation waits for the Assessment Map
    await unmount();
  }
});

test("a question whose time ran out says so on the same waiting screen", async () => {
  mockUseLiveQuiz.mockReturnValue(quizState(answered("timeout")));
  await render(<LiveQuizScreen />);
  expect(screen.getByText("Trainer...")).toBeTruthy();
  expect(screen.getByText(/Time's up for this question\./)).toBeTruthy();
});

test("before any question the waiting screen shows as before", async () => {
  mockUseLiveQuiz.mockReturnValue(quizState(null));
  await render(<LiveQuizScreen />);
  expect(screen.getByText("Trainer...")).toBeTruthy();
  expect(screen.queryByText(/Your answer is saved\./)).toBeNull();
});

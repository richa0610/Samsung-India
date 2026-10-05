import { afterEach, beforeAll, beforeEach, expect, jest, test } from "@jest/globals";
import { act, fireEvent, render, screen } from "@testing-library/react-native";

import LoginLandingScreen from "@/components/auth/LoginLandingScreen";
import { SLIDE_INTERVAL_MS } from "@/components/auth/login/LoginHero";
import { BRAND, LOGIN_ROLE_TEXT, LOGIN_TEXT } from "@/constants/strings";

const mockPush = jest.fn();

jest.mock("expo-router", () => ({
  useRouter: () => ({ push: mockPush, replace: jest.fn(), back: jest.fn() }),
}));
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 24, bottom: 0, left: 0, right: 0 }),
}));

// The first render loads the icon set and svg from scratch; do it once here, so each test below
// runs within the normal per-test limit.
beforeAll(async () => {
  const first = await render(<LoginLandingScreen />);
  await first.unmount();
}, 30_000);

beforeEach(() => {
  mockPush.mockReset();
  jest.useFakeTimers();
});
afterEach(() => {
  jest.useRealTimers();
});

const selectedDot = () =>
  LOGIN_TEXT.slides.findIndex((_, i) => screen.getByTestId(`login-slide-dot-${i}`).props.accessibilityState?.selected);

test("it carries the TOPS brand and the participant login wording - no Samsung", async () => {
  await render(<LoginLandingScreen />);
  expect(screen.getAllByLabelText(BRAND.name)).toHaveLength(2); // the hero and the footer wordmarks
  expect(screen.queryByText(/samsung/i)).toBeNull();
  expect(screen.queryByText(/india/i)).toBeNull();

  expect(screen.getByText(LOGIN_TEXT.title)).toBeTruthy();
  expect(screen.getByText(LOGIN_TEXT.subtitle)).toBeTruthy();
  expect(screen.getByText(LOGIN_TEXT.slides[0].headline)).toBeTruthy();
  expect(screen.getByText(BRAND.tagline.join("  |  "))).toBeTruthy();
});

const openRoleSheet = () => fireEvent.press(screen.getByLabelText(`${LOGIN_TEXT.staffPrompt} ${LOGIN_TEXT.staffLink}`));
const roleCard = (role: "trainer" | "admin") =>
  screen.getByLabelText(`${LOGIN_ROLE_TEXT[role].title}. ${LOGIN_ROLE_TEXT[role].body}`);
// The sheet slides away before it unmounts.
const finishSheetAnimation = () => act(async () => jest.advanceTimersByTime(1000));

test("participants go straight to their login: QR scan, or Company ID / phone", async () => {
  await render(<LoginLandingScreen />);

  await fireEvent.press(screen.getByLabelText(LOGIN_TEXT.viaQr));
  expect(mockPush).toHaveBeenLastCalledWith("/scan");

  await fireEvent.press(screen.getByLabelText(LOGIN_TEXT.viaUsername));
  expect(mockPush).toHaveBeenLastCalledWith("/participant_login");
});

test("Login here asks trainer or admin first, then opens that login", async () => {
  await render(<LoginLandingScreen />);
  expect(screen.queryByText(LOGIN_ROLE_TEXT.title)).toBeNull();

  await openRoleSheet();
  expect(screen.getByText(LOGIN_ROLE_TEXT.title)).toBeTruthy();
  expect(screen.getByText(LOGIN_ROLE_TEXT.subtitle)).toBeTruthy();
  expect(mockPush).not.toHaveBeenCalled();

  await fireEvent.press(roleCard("trainer"));
  expect(mockPush).toHaveBeenLastCalledWith("/trainer_login");
  await finishSheetAnimation();
  expect(screen.queryByText(LOGIN_ROLE_TEXT.title)).toBeNull();

  await openRoleSheet();
  await fireEvent.press(roleCard("admin"));
  expect(mockPush).toHaveBeenLastCalledWith({ pathname: "/trainer_login", params: { portal: "admin" } });
});

test("Cancel and the close button dismiss the sheet without going anywhere", async () => {
  await render(<LoginLandingScreen />);

  await openRoleSheet();
  await fireEvent.press(screen.getByLabelText(LOGIN_ROLE_TEXT.cancel));
  await finishSheetAnimation();
  expect(screen.queryByText(LOGIN_ROLE_TEXT.title)).toBeNull();

  await openRoleSheet();
  await fireEvent.press(screen.getByLabelText(LOGIN_ROLE_TEXT.close));
  await finishSheetAnimation();
  expect(screen.queryByText(LOGIN_ROLE_TEXT.title)).toBeNull();
  expect(mockPush).not.toHaveBeenCalled();
});

test("the carousel has a dot per slide, moves on by itself, and a dot jumps to its slide", async () => {
  await render(<LoginLandingScreen />);
  expect(selectedDot()).toBe(0);

  await act(async () => jest.advanceTimersByTime(SLIDE_INTERVAL_MS));
  expect(selectedDot()).toBe(1);

  await fireEvent.press(screen.getByTestId("login-slide-dot-2"));
  expect(selectedDot()).toBe(2);

  await act(async () => jest.advanceTimersByTime(SLIDE_INTERVAL_MS));
  expect(selectedDot()).toBe(0); // wraps back to the first slide
});

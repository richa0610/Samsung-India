import { beforeAll, beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";
import { Alert } from "react-native";

import { loginAdmin } from "@/api/admin";
import StaffLoginScreen from "@/components/auth/staff-login/StaffLoginScreen";
import { STAFF_LOGIN_TEXT } from "@/constants/strings";

const mockRouter = { back: jest.fn(), replace: jest.fn(), push: jest.fn(), canGoBack: jest.fn(() => true) };
const mockSetAdminSession = jest.fn();

jest.mock("expo-router", () => ({ useRouter: () => mockRouter }));
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 24, bottom: 0, left: 0, right: 0 }),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ setAdminSession: mockSetAdminSession }) }));
jest.mock("@/api/admin", () => ({
  ...jest.requireActual<object>("@/api/admin"),
  loginAdmin: jest.fn(),
}));

const mockLogin = jest.mocked(loginAdmin);

// The first render loads the icon set and svg from scratch; do it once here, so each test below
// runs within the normal per-test limit.
beforeAll(async () => {
  const first = await render(<StaffLoginScreen portal="trainer" />);
  await first.unmount();
}, 30_000);

beforeEach(() => {
  jest.clearAllMocks();
  mockRouter.canGoBack.mockReturnValue(true);
});

test("the trainer screen carries the trainer wording, the brand and the secure note", async () => {
  await render(<StaffLoginScreen portal="trainer" />);
  const t = STAFF_LOGIN_TEXT.trainer;
  expect(screen.getAllByText(t.tag).length).toBeGreaterThanOrEqual(1); // the tag and the card title
  expect(screen.getByText(t.headline)).toBeTruthy();
  expect(screen.getByText(t.headlineAccent)).toBeTruthy();
  expect(screen.getByText(t.idLabel)).toBeTruthy();
  expect(screen.getByPlaceholderText(t.idPlaceholder)).toBeTruthy();
  expect(screen.getByPlaceholderText(STAFF_LOGIN_TEXT.passwordPlaceholder)).toBeTruthy();
  expect(screen.getByLabelText(t.submit)).toBeTruthy();
  expect(screen.getByText(STAFF_LOGIN_TEXT.secureTitle)).toBeTruthy();
  expect(screen.getByLabelText("TOPS")).toBeTruthy();
});


test("the admin screen is worded for admins", async () => {
  await render(<StaffLoginScreen portal="admin" />);
  const a = STAFF_LOGIN_TEXT.admin;
  expect(screen.getByText(a.headline)).toBeTruthy();
  expect(screen.getByText(a.idLabel)).toBeTruthy();
  expect(screen.getByLabelText(a.submit)).toBeTruthy();
  expect(screen.queryByText(STAFF_LOGIN_TEXT.trainer.idLabel)).toBeNull();
});

test("signing in sends a trainer to the trainer dashboard", async () => {
  mockLogin.mockResolvedValue({ access_token: "t", admin: { role: "trainer" } } as never);
  await render(<StaffLoginScreen portal="trainer" />);

  await fireEvent.changeText(screen.getByPlaceholderText(STAFF_LOGIN_TEXT.trainer.idPlaceholder), "9100000001");
  await fireEvent.changeText(screen.getByPlaceholderText(STAFF_LOGIN_TEXT.passwordPlaceholder), "secret");
  await fireEvent.press(screen.getByLabelText(STAFF_LOGIN_TEXT.trainer.submit));

  await waitFor(() => expect(mockRouter.replace).toHaveBeenCalledWith("/trainer_dashboard"));
  expect(mockLogin).toHaveBeenCalledWith("9100000001", "secret");
  expect(mockSetAdminSession).toHaveBeenCalled();
});

test("an empty form isn't sent; a session-expired notice shows on arrival", async () => {
  await render(<StaffLoginScreen portal="trainer" reason="session_expired" />);
  expect(screen.getByText("Your session expired. Please log in again.")).toBeTruthy();

  await fireEvent.press(screen.getByLabelText(STAFF_LOGIN_TEXT.trainer.submit));
  expect(mockLogin).not.toHaveBeenCalled();
  expect(screen.getByText("Enter your username and password.")).toBeTruthy();
});

test("Forgot password points to the administrator, and Back goes back", async () => {
  const alert = jest.spyOn(Alert, "alert").mockImplementation(() => {});
  await render(<StaffLoginScreen portal="trainer" />);

  await fireEvent.press(screen.getByText(STAFF_LOGIN_TEXT.forgot));
  expect(alert).toHaveBeenCalledWith(STAFF_LOGIN_TEXT.forgotTitle, STAFF_LOGIN_TEXT.forgotMessage);

  await fireEvent.press(screen.getByLabelText(STAFF_LOGIN_TEXT.back));
  expect(mockRouter.back).toHaveBeenCalled();
  alert.mockRestore();
});

test("Back from a deep link (nothing to go back to) lands on the login landing", async () => {
  mockRouter.canGoBack.mockReturnValue(false);
  await render(<StaffLoginScreen portal="trainer" />);
  await fireEvent.press(screen.getByLabelText(STAFF_LOGIN_TEXT.back));
  expect(mockRouter.replace).toHaveBeenCalledWith("/");
});

test("each role has its own background scene", async () => {
  const sourceOf = () => JSON.stringify(screen.getByTestId("staff-login-background").props.source);
  const trainer = await render(<StaffLoginScreen portal="trainer" />);
  expect(sourceOf()).toContain("trainer_bg");
  await trainer.unmount();

  await render(<StaffLoginScreen portal="admin" />);
  expect(sourceOf()).toContain("admin_bg");
});

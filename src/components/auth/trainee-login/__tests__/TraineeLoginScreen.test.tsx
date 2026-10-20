import { beforeAll, beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import { loginTrainee } from "@/api/auth";
import TraineeLoginScreen from "@/components/auth/trainee-login/TraineeLoginScreen";
import { setCompany } from "@/config/company";
import { SESSION_EXPIRED_NOTICE, STAFF_LOGIN_TEXT } from "@/constants/strings";

const mockRouter = { back: jest.fn(), replace: jest.fn(), push: jest.fn(), canGoBack: jest.fn(() => true) };
const mockSetSession = jest.fn();
let mockParams: Record<string, string> = {};

jest.mock("expo-router", () => ({
  useRouter: () => mockRouter,
  useLocalSearchParams: () => mockParams,
}));
jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 24, bottom: 0, left: 0, right: 0 }),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ setSession: mockSetSession }) }));
jest.mock("@/api/auth", () => ({
  ...jest.requireActual<object>("@/api/auth"),
  loginTrainee: jest.fn(),
}));

const mockLogin = jest.mocked(loginTrainee);

beforeAll(async () => {
  setCompany({ tenantId: "acme", companyName: "Acme Retail" }); // sign-in screens need the company first
  const first = await render(<TraineeLoginScreen />);
  await first.unmount();
}, 30_000);

beforeEach(() => {
  jest.clearAllMocks();
  mockRouter.canGoBack.mockReturnValue(true);
  mockParams = {};
});

test("sent here because the sign-in ended: says so", async () => {
  mockParams = { reason: "session_expired" };
  await render(<TraineeLoginScreen />);
  expect(screen.getByText(SESSION_EXPIRED_NOTICE)).toBeTruthy();
});

test("arriving normally shows no such notice", async () => {
  await render(<TraineeLoginScreen />);
  expect(screen.queryByText(SESSION_EXPIRED_NOTICE)).toBeNull();
});

test("renders the brand, hero text, trainee login card, and security badge", async () => {
  await render(<TraineeLoginScreen />);

  expect(screen.getByLabelText("TOPS")).toBeTruthy();
  expect(screen.queryByText("INDIA")).toBeNull();
  expect(screen.getByText("Skip")).toBeTruthy();


  expect(screen.getByText("Learn.")).toBeTruthy();
  expect(screen.getByText("Assess.")).toBeTruthy();
  expect(screen.getByText("Grow together.")).toBeTruthy();

  expect(screen.getByText("Trainee Login")).toBeTruthy();
  expect(screen.getByText("Enter your credentials to continue")).toBeTruthy();
  expect(screen.getByText("Company ID / Phone No")).toBeTruthy();
  expect(screen.getByPlaceholderText("Enter Company ID or Phone No")).toBeTruthy();
  expect(screen.getByPlaceholderText("Enter password")).toBeTruthy();
  expect(screen.getByText(STAFF_LOGIN_TEXT.forgot)).toBeTruthy();
  expect(screen.getByLabelText("Login as Trainee")).toBeTruthy();
  expect(screen.getByText("Your information is secure")).toBeTruthy();
});

test("the Company ID / Phone No field takes at most 10 characters", async () => {
  await render(<TraineeLoginScreen />);
  expect(screen.getByPlaceholderText("Enter Company ID or Phone No").props.maxLength).toBe(10);
});

test("successfully signs in a trainee with company id / phone", async () => {
  mockLogin.mockResolvedValueOnce({
    access_token: "fake-trainee-token",
    token_type: "bearer",
    trainee: {
      id: 1,
      traineeUid: "TRN100",
      name: "Trainee User",
      phone: 9876543210,
      email: "trainee@example.com",
      gender: null,
      designation: null,
      employee_id: null,
      supervisorName: null,
      state: "Delhi",
      district: null,
      profilePhoto: null,
      status: "Approved",
    },
  });

  await render(<TraineeLoginScreen />);

  const phoneInput = screen.getByPlaceholderText("Enter Company ID or Phone No");
  await fireEvent.changeText(phoneInput, "9876543210");

  const passwordInput = screen.getByPlaceholderText("Enter password");
  await fireEvent.changeText(passwordInput, "password123");

  const submitButton = screen.getByLabelText("Login as Trainee");
  await fireEvent.press(submitButton);

  await waitFor(() => {
    expect(mockLogin).toHaveBeenCalledWith("9876543210", "password123");
  });
  expect(mockSetSession).toHaveBeenCalled();
  expect(mockRouter.replace).toHaveBeenCalledWith("/session_detail");
});

test("a Company ID with letters is kept as typed and sent with the password", async () => {
  mockLogin.mockRejectedValueOnce(new Error("offline"));
  await render(<TraineeLoginScreen />);

  await fireEvent.changeText(screen.getByPlaceholderText("Enter Company ID or Phone No"), " TRN2610001 ");
  await fireEvent.changeText(screen.getByPlaceholderText("Enter password"), "secret");
  await fireEvent.press(screen.getByLabelText("Login as Trainee"));

  await waitFor(() => {
    expect(mockLogin).toHaveBeenCalledWith("TRN2610001", "secret");
  });
});

test("the password is required", async () => {
  await render(<TraineeLoginScreen />);

  await fireEvent.changeText(screen.getByPlaceholderText("Enter Company ID or Phone No"), "9876543210");
  await fireEvent.press(screen.getByLabelText("Login as Trainee"));

  expect(await screen.findByText("Enter your password")).toBeTruthy();
  expect(mockLogin).not.toHaveBeenCalled();
});


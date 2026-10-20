import { beforeAll, beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import { ApiError, CompanyChoice, chooseLoginCompany } from "@/api/admin";
import ChooseCompanyScreen from "@/components/auth/choose-company/ChooseCompanyScreen";
import { CHOOSE_COMPANY_TEXT } from "@/constants/strings";
import { getCompanyChoice, setCompanyChoice } from "@/services/companyChoice";

const mockRouter = { back: jest.fn(), replace: jest.fn(), push: jest.fn() };
const mockSetAdminSession = jest.fn();

jest.mock("expo-router", () => ({ useRouter: () => mockRouter }));
jest.mock("react-native-safe-area-context", () => ({
  useSafeAreaInsets: () => ({ top: 24, bottom: 0, left: 0, right: 0 }),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ setAdminSession: mockSetAdminSession }) }));
jest.mock("@/api/admin", () => ({
  ...jest.requireActual<object>("@/api/admin"),
  chooseLoginCompany: jest.fn(),
}));

const mockChoose = jest.mocked(chooseLoginCompany);
const CHOICE: CompanyChoice = {
  code: "CHOOSE_COMPANY",
  message: "Choose the company to sign in to",
  companies: [{ tenantId: "samsung", companyName: "Samsung India" }, { tenantId: "demo", companyName: "Demo Co" }],
  ticket: "a-ticket",
};

beforeAll(async () => {
  setCompanyChoice(CHOICE);
  const first = await render(<ChooseCompanyScreen />);   // loads the icon set once
  await first.unmount();
}, 30_000);

beforeEach(() => {
  jest.clearAllMocks();
  setCompanyChoice(CHOICE);
});

test("it lists the companies the sign-in was answered with", async () => {
  await render(<ChooseCompanyScreen />);
  expect(screen.getByText(CHOOSE_COMPANY_TEXT.title)).toBeTruthy();
  expect(screen.getByLabelText("Samsung India")).toBeTruthy();
  expect(screen.getByLabelText("Demo Co")).toBeTruthy();
});

test("picking one signs in to it with the ticket and opens the dashboard", async () => {
  mockChoose.mockResolvedValue({ access_token: "t", token_type: "bearer", admin: { role: "admin" } } as never);
  await render(<ChooseCompanyScreen />);
  await fireEvent.press(screen.getByLabelText("Demo Co"));

  await waitFor(() => expect(mockRouter.replace).toHaveBeenCalledWith("/admin_dashboard"));
  expect(mockChoose).toHaveBeenCalledWith("a-ticket", "demo");
  expect(mockSetAdminSession).toHaveBeenCalled();
  expect(getCompanyChoice()).toBeNull();   // a ticket is used once
});

test("an expired ticket says so and signs nobody in", async () => {
  mockChoose.mockRejectedValue(new ApiError(CHOOSE_COMPANY_TEXT.expired, 401));
  await render(<ChooseCompanyScreen />);
  await fireEvent.press(screen.getByLabelText("Samsung India"));

  expect(await screen.findByText(CHOOSE_COMPANY_TEXT.expired)).toBeTruthy();
  expect(mockSetAdminSession).not.toHaveBeenCalled();
});

test("opened without a pending choice it goes back to the staff login", async () => {
  setCompanyChoice(null);
  await render(<ChooseCompanyScreen />);
  expect(mockRouter.replace).toHaveBeenCalledWith("/trainer_login");
});

import { beforeEach, expect, jest, test } from "@jest/globals";
import { render, screen, waitFor } from "@testing-library/react-native";

import HomeScreen from "@/app/index";

const mockRouter = { replace: jest.fn(), push: jest.fn(), back: jest.fn() };
let mockAuthState = {
  restoring: true,
  token: null as string | null,
  adminToken: null as string | null,
  admin: null as { role: string } | null,
};

jest.mock("expo-router", () => ({
  useRouter: () => mockRouter,
}));

jest.mock("@/hooks/useAuth", () => ({
  useAuth: () => mockAuthState,
}));

jest.mock("@/components/auth/LoginLandingScreen", () => {
  const { View } = require("react-native");
  return () => <View testID="mock-login" />;
});
jest.mock("@/components/common/BrandSplash", () => {
  const { View } = require("react-native");
  return () => <View testID="mock-splash" />;
});

beforeEach(() => {
  mockRouter.replace.mockReset();
  mockAuthState = {
    restoring: true,
    token: null,
    adminToken: null,
    admin: null,
  };
});

test("shows BrandSplash while restoring session from storage", async () => {
  mockAuthState = { restoring: true, token: null, adminToken: null, admin: null };
  await render(<HomeScreen />);
  expect(screen.getByTestId("mock-splash")).toBeTruthy();
  expect(mockRouter.replace).not.toHaveBeenCalled();
});

test("redirects logged-in admin to /admin_dashboard", async () => {
  mockAuthState = {
    restoring: false,
    token: null,
    adminToken: "admin-jwt-token",
    admin: { role: "admin" },
  };
  await render(<HomeScreen />);
  await waitFor(() => {
    expect(mockRouter.replace).toHaveBeenCalledWith("/admin_dashboard");
  });
  expect(screen.getByTestId("mock-splash")).toBeTruthy();
});

test("redirects logged-in trainer to /trainer_dashboard", async () => {
  mockAuthState = {
    restoring: false,
    token: null,
    adminToken: "trainer-jwt-token",
    admin: { role: "trainer" },
  };
  await render(<HomeScreen />);
  await waitFor(() => {
    expect(mockRouter.replace).toHaveBeenCalledWith("/trainer_dashboard");
  });
  expect(screen.getByTestId("mock-splash")).toBeTruthy();
});

test("redirects logged-in trainee to /session_detail", async () => {
  mockAuthState = {
    restoring: false,
    token: "trainee-jwt-token",
    adminToken: null,
    admin: null,
  };
  await render(<HomeScreen />);
  await waitFor(() => {
    expect(mockRouter.replace).toHaveBeenCalledWith("/session_detail");
  });
  expect(screen.getByTestId("mock-splash")).toBeTruthy();
});

test("renders LoginLandingScreen when user is not authenticated and restoring is finished", async () => {
  mockAuthState = {
    restoring: false,
    token: null,
    adminToken: null,
    admin: null,
  };
  await render(<HomeScreen />);
  expect(mockRouter.replace).not.toHaveBeenCalled();
  expect(screen.getByTestId("mock-login")).toBeTruthy();
});

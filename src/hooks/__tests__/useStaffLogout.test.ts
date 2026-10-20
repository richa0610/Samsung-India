import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook } from "@testing-library/react-native";
import { BackHandler, HardwareBackPressEvent } from "react-native";

import { useStaffLogout } from "@/hooks/useStaffLogout";

const mockReplace = jest.fn();
const mockAdminLogout = jest.fn();

jest.mock("expo-router", () => ({
  useRouter: () => ({ replace: mockReplace, push: jest.fn(), back: jest.fn() }),
  // Treat the screen as focused for as long as the hook is mounted.
  useFocusEffect: (callback: () => void | (() => void)) => require("react").useEffect(callback, [callback]),
}));
jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminLogout: mockAdminLogout }) }));

const mockRemove = jest.fn();
let backHandler: (event: HardwareBackPressEvent) => boolean | null | undefined = () => false;
const pressBack = () => backHandler({ type: "hardwareBackPress", timeStamp: Date.now() });

beforeEach(() => {
  jest.restoreAllMocks(); // a fresh BackHandler spy per test, so call counts don't carry over
  mockReplace.mockReset();
  mockAdminLogout.mockReset();
  mockRemove.mockReset();
  jest.spyOn(BackHandler, "addEventListener").mockImplementation((_event, handler) => {
    backHandler = handler;
    return { remove: mockRemove };
  });
});

test("the power button only asks; cancelling keeps the user signed in", async () => {
  const { result } = await renderHook(() => useStaffLogout());
  expect(result.current.confirmLogoutOpen).toBe(false);

  await act(() => result.current.requestLogout());
  expect(result.current.confirmLogoutOpen).toBe(true);

  await act(() => result.current.cancelLogout());
  expect(result.current.confirmLogoutOpen).toBe(false);
  expect(mockAdminLogout).not.toHaveBeenCalled();
  expect(mockReplace).not.toHaveBeenCalled();
});

test("confirming signs out and lands on the role chooser", async () => {
  const { result } = await renderHook(() => useStaffLogout());

  await act(() => result.current.requestLogout());
  await act(() => result.current.confirmLogout());

  expect(mockAdminLogout).toHaveBeenCalledTimes(1);
  expect(mockReplace).toHaveBeenCalledWith("/");
  expect(result.current.confirmLogoutOpen).toBe(false);
});

test("the phone's back button opens the same confirmation instead of leaving", async () => {
  const { result } = await renderHook(() => useStaffLogout());

  let handled: boolean | null | undefined;
  await act(() => {
    handled = pressBack();
  });

  expect(handled).toBe(true); // consumed - the screen stays put
  expect(result.current.confirmLogoutOpen).toBe(true);
  expect(mockAdminLogout).not.toHaveBeenCalled();
});

test("screens that opt out keep the normal back button but still confirm logout", async () => {
  const addListener = jest.mocked(BackHandler.addEventListener);
  const { result } = await renderHook(() => useStaffLogout({ confirmOnBack: false }));
  expect(addListener).not.toHaveBeenCalled();

  await act(() => result.current.requestLogout());
  expect(result.current.confirmLogoutOpen).toBe(true);
  await act(() => result.current.confirmLogout());
  expect(mockAdminLogout).toHaveBeenCalledTimes(1);
  expect(mockReplace).toHaveBeenCalledWith("/");
});

test("the back-button handler is released when the screen goes away", async () => {
  const { unmount } = await renderHook(() => useStaffLogout());
  expect(mockRemove).not.toHaveBeenCalled();

  await unmount();
  expect(mockRemove).toHaveBeenCalledTimes(1);
});

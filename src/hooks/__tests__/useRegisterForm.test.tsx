import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook } from "@testing-library/react-native";

import { loginTrainee, registerTrainee } from "@/api/auth";
import { joinSession } from "@/api/session";
import { useRegisterForm } from "@/hooks/useRegisterForm";

const mockSetSession = jest.fn();

jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ setSession: mockSetSession }) }));
jest.mock("@/api/auth", () => ({
  ...jest.requireActual<object>("@/api/auth"),
  registerTrainee: jest.fn(),
  loginTrainee: jest.fn(),
}));
jest.mock("@/api/session", () => ({ joinSession: jest.fn() }));

const mockRegister = jest.mocked(registerTrainee);
const mockJoin = jest.mocked(joinSession);
const SESSION = { access_token: "new-trainee-token", token_type: "bearer", trainee: { phone: 9876543210 } } as never;

beforeEach(() => {
  jest.clearAllMocks();
  mockRegister.mockResolvedValue(SESSION);
  mockJoin.mockResolvedValue(undefined as never);
});

async function submit(joinCode?: string, place: { zone?: string; region?: string } = {}) {
  const onSuccess = jest.fn();
  const { result } = await renderHook(() => useRegisterForm({ joinCode, onSuccess }));
  await act(async () => {
    result.current.setValue("name", "New Person");
    result.current.setValue("phone", "9876543210");
    result.current.setValue("email", "new.person@example.com");
    result.current.setValue("state", "Delhi");
    if (place.zone) result.current.setValue("zone", place.zone);
    if (place.region) result.current.setValue("region", place.region);
  });
  await act(async () => {
    await result.current.onSubmit();
  });
  return onSuccess;
}

test("a QR sign-up is signed in by the registration itself and joins the scanned session", async () => {
  const onSuccess = await submit("CONF2610010001.abc");

  expect(mockSetSession).toHaveBeenCalledWith(SESSION);
  expect(mockJoin).toHaveBeenCalledWith("CONF2610010001.abc", "new-trainee-token", true);
  expect(loginTrainee).not.toHaveBeenCalled();   // no password to log in with
  expect(onSuccess).toHaveBeenCalled();
});

test("the zone and region picked are sent - the zone starts the trainee's ID", async () => {
  await submit(undefined, { zone: "South", region: "South 1" });

  expect(mockRegister).toHaveBeenCalledWith(expect.objectContaining({ zone: "South", region: "South 1" }));
});

test("a sign-up without a QR is signed in too, and joins nothing", async () => {
  const onSuccess = await submit();

  expect(mockSetSession).toHaveBeenCalledWith(SESSION);
  expect(mockJoin).not.toHaveBeenCalled();
  expect(onSuccess).toHaveBeenCalled();
});

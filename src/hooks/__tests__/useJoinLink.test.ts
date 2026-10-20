import { beforeEach, expect, jest, test } from "@jest/globals";
import { act, renderHook, waitFor } from "@testing-library/react-native";

import { fetchJoinLink } from "@/api/training";
import { useJoinLink } from "@/hooks/useJoinLink";

jest.mock("@/hooks/useAuth", () => ({ useAuth: () => ({ adminToken: "trainer-token" }) }));
jest.mock("@/api/training", () => ({ fetchJoinLink: jest.fn() }));

const mockFetch = jest.mocked(fetchJoinLink);

beforeEach(() => {
  mockFetch.mockReset();
});

test("nothing is fetched until the QR is opened, then the signed link arrives", async () => {
  mockFetch.mockResolvedValue("samsungindia://join/CONF1.SIG");
  const { result, rerender } = await renderHook(({ open }: { open: boolean }) => useJoinLink("CONF1", open), {
    initialProps: { open: false },
  });
  expect(mockFetch).not.toHaveBeenCalled();
  expect(result.current.link).toBeNull();

  await rerender({ open: true });
  expect(result.current.loading || result.current.link !== null).toBe(true); // loading, or already arrived
  await waitFor(() => expect(result.current.link).toBe("samsungindia://join/CONF1.SIG"));
  expect(mockFetch).toHaveBeenCalledWith("trainer-token", "CONF1");
});

test("a failure can be retried", async () => {
  mockFetch.mockRejectedValueOnce(new Error("offline"));
  mockFetch.mockResolvedValueOnce("samsungindia://join/CONF1.SIG");
  const { result } = await renderHook(() => useJoinLink("CONF1", true));
  await waitFor(() => expect(result.current.failed).toBe(true));
  expect(result.current.link).toBeNull();

  await act(() => result.current.retry());
  await waitFor(() => expect(result.current.link).toBe("samsungindia://join/CONF1.SIG"));
});

test("a link for another training is never shown", async () => {
  mockFetch.mockImplementation(async (_token, uid) => `samsungindia://join/${uid}.SIG`);
  const { result, rerender } = await renderHook(({ uid }: { uid: string }) => useJoinLink(uid, true), {
    initialProps: { uid: "CONF1" },
  });
  await waitFor(() => expect(result.current.link).toBe("samsungindia://join/CONF1.SIG"));
  await rerender({ uid: "CONF2" });
  expect(result.current.link === null || result.current.link.includes("CONF2")).toBe(true);
  await waitFor(() => expect(result.current.link).toBe("samsungindia://join/CONF2.SIG"));
});

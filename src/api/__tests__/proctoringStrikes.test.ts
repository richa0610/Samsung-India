import { beforeEach, describe, expect, jest, test } from "@jest/globals";
import { newStrikeId, reportProctoringLock, reportProctoringViolation } from "@/api/session";

// What the server accepts as a strike ID (backend/app/schemas/session.py: StrikeId).
const SERVER_STRIKE_ID = /^[A-Za-z0-9_-]{8,64}$/;

describe("proctoring strike reports", () => {
  const fetchMock = jest.fn<(...args: any[]) => Promise<any>>();

  beforeEach(() => {
    fetchMock.mockReset();
    fetchMock.mockResolvedValue({ ok: true, json: async () => ({ counted: true, attemptsLeft: 2, locked: false }) });
    global.fetch = fetchMock as unknown as typeof fetch;
  });

  test("every strike ID is one the server accepts, and none repeats", () => {
    const ids = Array.from({ length: 500 }, () => newStrikeId());
    ids.forEach((id) => expect(id).toMatch(SERVER_STRIKE_ID));
    expect(new Set(ids).size).toBe(ids.length);
  });

  test("a strike is sent with its ID", async () => {
    await reportProctoringViolation("tok", "CONF1", "NO FACE DETECTED", "abc12345-xyz");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/sessions\/proctoring-violation$/);
    expect(JSON.parse(init.body as string)).toEqual({
      conferenceUid: "CONF1",
      violationType: "NO FACE DETECTED",
      strikeId: "abc12345-xyz",
    });
  });

  test("the lockout carries the locking strike's ID", async () => {
    await reportProctoringLock("tok", "CONF1", "NO FACE DETECTED", 3, "abc12345-xyz");
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toMatch(/\/sessions\/proctoring-lock$/);
    expect(JSON.parse(init.body as string)).toEqual({
      conferenceUid: "CONF1",
      violationType: "NO FACE DETECTED",
      strikeNumber: 3,
      strikeId: "abc12345-xyz",
    });
  });
});

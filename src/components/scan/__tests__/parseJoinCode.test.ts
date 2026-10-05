import { describe, expect, test } from "@jest/globals";

import { redirectSystemPath } from "@/app/+native-intent";
import { parseJoinCode } from "@/components/scan/parseJoinCode";

const SIGNED = "CONF2698735081.K3J9XQ2M7PLA4TZB";
const OLD = "CONF2610035";

describe("a scanned QR / shared link keeps the whole join code", () => {
  test.each([
    [`samsungindia://join/${SIGNED}`, SIGNED],
    [`/join/${SIGNED}`, SIGNED],
    [SIGNED, SIGNED],
    [`  ${SIGNED}  `, SIGNED],
    [`samsungindia://join/${OLD}`, OLD], // an older unsigned QR (accepted by the server for a while)
    [OLD, OLD],
    ["hello world", null],
  ])("%s", (raw, expected) => {
    expect(parseJoinCode(raw)).toBe(expected);
  });
});

describe("deep links route to the join screen with the whole code", () => {
  test.each([
    [`samsungindia://join/${SIGNED}`, `/join/${SIGNED}`],
    [`exp://192.168.1.5:8081/--/join/${SIGNED}`, `/join/${SIGNED}`],
    [`samsungindia:///${SIGNED}`, `/join/${SIGNED}`], // authority dropped by some Android versions
    [`samsungindia:///${OLD}`, `/join/${OLD}`],
    ["samsungindia://trainee_dashboard", "samsungindia://trainee_dashboard"],
  ])("%s", (path, expected) => {
    expect(redirectSystemPath({ path, initial: true })).toBe(expected);
  });
});

import { describe, expect, test } from "@jest/globals";

import { redirectSystemPath } from "@/app/+native-intent";
import { parseJoinLink } from "@/components/scan/parseJoinLink";

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
  ])("%s", (raw, code) => {
    expect(parseJoinLink(raw)).toEqual({ code, company: null });
  });

  test("something that isn't a join link", () => {
    expect(parseJoinLink("hello world")).toBeNull();
  });
});

describe("a link names the company its training belongs to", () => {
  test.each([
    [`samsungindia://join/${SIGNED}?company=samsung`, "samsung"],
    [`samsungindia://join/${SIGNED}?company=TEN_DEM_2620001`, "TEN_DEM_2620001"],
    [`samsungindia://join/${SIGNED}?x=1&company=demo%20co`, "demo co"],
    [`samsungindia://join/${SIGNED}?company=%E0%A4`, null], // can't be decoded: no company
  ])("%s", (raw, company) => {
    expect(parseJoinLink(raw)).toEqual({ code: SIGNED, company });
  });
});

describe("deep links route to the join screen with the whole code - and its company", () => {
  test.each([
    [`samsungindia://join/${SIGNED}`, `/join/${SIGNED}`],
    [`exp://192.168.1.5:8081/--/join/${SIGNED}`, `/join/${SIGNED}`],
    [`samsungindia:///${SIGNED}`, `/join/${SIGNED}`], // authority dropped by some Android versions
    [`samsungindia:///${OLD}`, `/join/${OLD}`],
    [`samsungindia://join/${SIGNED}?company=samsung`, `/join/${SIGNED}?company=samsung`],
    [`samsungindia:///${SIGNED}?company=demo`, `/join/${SIGNED}?company=demo`],
    [`samsungindia://join/${SIGNED}?flow=JOINED&company=demo`, `/join/${SIGNED}?company=demo`], // nothing else passes
    ["samsungindia://trainee_dashboard", "samsungindia://trainee_dashboard"],
  ])("%s", (path, expected) => {
    expect(redirectSystemPath({ path, initial: true })).toBe(expected);
  });
});

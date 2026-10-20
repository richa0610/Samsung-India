import { expect, test } from "@jest/globals";

import {
  clearPendingCheckIn,
  getPendingCheckIn,
  getSessionFlowState,
  isModuleLeft,
  markModuleLeft,
  setAttendanceState,
  setPendingCheckIn,
  setSessionFlowState,
} from "@/services/sessionFlowState";

test("each training keeps its own check-in progress, starting at JOINED", () => {
  expect(getSessionFlowState("CONF-A", "TRN1")).toBe("JOINED");
  setSessionFlowState("CAMERA_VERIFIED", "CONF-A", "TRN1");
  expect(getSessionFlowState("CONF-A", "TRN1")).toBe("CAMERA_VERIFIED");
  expect(getSessionFlowState("CONF-B", "TRN1")).toBe("JOINED");
});

test("recorded attendance sticks through later steps until the trainee rejoins", () => {
  setAttendanceState("ATTENDANCE_RECORDED", "CONF-C", "TRN1");
  setSessionFlowState("ACCESS_GRANTED", "CONF-C", "TRN1");
  expect(getSessionFlowState("CONF-C", "TRN1")).toBe("ATTENDANCE_RECORDED");
  setSessionFlowState("JOINED", "CONF-C", "TRN1");
  expect(getSessionFlowState("CONF-C", "TRN1")).toBe("JOINED");
});

test("a module left is remembered per training and trainee", () => {
  markModuleLeft("CONF-D", "LIVE_QUIZ", "TRN1");
  expect(isModuleLeft("CONF-D", "LIVE_QUIZ", "TRN1")).toBe(true);
  expect(isModuleLeft("CONF-D", "LIVE_QUIZ", "TRN2")).toBe(false);
});

test("the pending check-in is held until cleared", () => {
  setPendingCheckIn({ latitude: 28.6, longitude: 77.2, photoUri: "file:///photo.jpg" });
  expect(getPendingCheckIn()).toEqual({ latitude: 28.6, longitude: 77.2, photoUri: "file:///photo.jpg" });
  clearPendingCheckIn();
  expect(getPendingCheckIn()).toBeNull();
});

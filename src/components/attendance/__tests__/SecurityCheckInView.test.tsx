import { beforeEach, expect, jest, test } from "@jest/globals";
import { fireEvent, render, screen, waitFor } from "@testing-library/react-native";

import SecurityCheckInView from "../SecurityCheckInView";

type CameraState = { hasPhoto: boolean; photoSource: { uri: string } | null };
type ViewfinderProps = { extraOutputs?: unknown[]; overlay?: unknown };

const mockHandleCapture = jest.fn(async () => {});
const mockVerifyCapturedPhoto = jest.fn(async () => ({ ok: true, faceCount: 1 }));
const mockGateCalls: { active: boolean }[] = [];
const mockDetectorOutput = { detector: true };
let mockCamera: CameraState = { hasPhoto: false, photoSource: null };
let mockVerified = false;
let mockViewfinder: ViewfinderProps = {};

jest.mock("react-native-safe-area-context", () => ({
  SafeAreaView: require("react-native").View,
  useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
}));
jest.mock("@/components/liveness-check", () => ({
  useFaceLivenessGate: (params: { active: boolean }) => {
    mockGateCalls.push(params);
    return {
      verified: mockVerified,
      step: "PLACE_FACE",
      instruction: "Place your face in the frame",
      detectorError: null,
      faceDetectorOutput: mockDetectorOutput,
      reset: jest.fn(),
      verifyCapturedPhoto: mockVerifyCapturedPhoto,
    };
  },
  LivenessInstructionOverlay: () => null,
}));
jest.mock("@/components/attendance/security-checkin/useSecurityCheckIn", () => ({
  useSecurityCheckIn: () => ({
    hasPermission: true,
    requestPermission: jest.fn(),
    device: {},
    deviceTimedOut: false,
    retryDevice: jest.fn(),
    photoOutput: {},
    cameraRef: { current: null },
    capturing: false,
    handleCapture: mockHandleCapture,
    handleRetake: jest.fn(),
    ...mockCamera,
  }),
}));
jest.mock("@/components/attendance/security-checkin/CameraViewfinder", () => ({
  __esModule: true,
  default: (props: ViewfinderProps) => {
    mockViewfinder = props;
    return null;
  },
}));

beforeEach(() => {
  mockHandleCapture.mockClear();
  mockVerifyCapturedPhoto.mockClear();
  mockGateCalls.length = 0;
  mockCamera = { hasPhoto: false, photoSource: null };
  mockVerified = false;
  mockViewfinder = {};
});

const captureButton = () => screen.getByLabelText("Capture Photo");

test("with face detection on, the face check runs and Capture waits for it", async () => {
  await render(<SecurityCheckInView onProceed={jest.fn()} />);

  expect(mockGateCalls.at(-1)).toEqual({ active: true });
  expect(mockViewfinder.extraOutputs).toEqual([mockDetectorOutput]);
  expect(mockViewfinder.overlay).toBeTruthy();
  expect(captureButton().props.accessibilityState?.disabled).toBe(true);

  await fireEvent.press(captureButton());
  expect(mockHandleCapture).not.toHaveBeenCalled();
});

test("with face detection off, the trainee just captures a photo", async () => {
  await render(<SecurityCheckInView onProceed={jest.fn()} faceDetection={false} />);

  expect(mockGateCalls.at(-1)).toEqual({ active: false });
  expect(mockViewfinder.extraOutputs).toBeUndefined();
  expect(mockViewfinder.overlay).toBeFalsy();
  expect(captureButton().props.accessibilityState?.disabled).toBe(false);

  await fireEvent.press(captureButton());
  await waitFor(() => expect(mockHandleCapture).toHaveBeenCalledTimes(1));
});

test("the captured photo is face-checked only when face detection is on", async () => {
  mockCamera = { hasPhoto: true, photoSource: { uri: "file:///photo.jpg" } };

  const off = await render(<SecurityCheckInView onProceed={jest.fn()} faceDetection={false} />);
  await off.unmount();
  expect(mockVerifyCapturedPhoto).not.toHaveBeenCalled();

  await render(<SecurityCheckInView onProceed={jest.fn()} />);
  await waitFor(() => expect(mockVerifyCapturedPhoto).toHaveBeenCalledWith("file:///photo.jpg"));
});

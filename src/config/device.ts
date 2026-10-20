import * as Device from "expo-device";
import { Platform } from "react-native";

import { persistedText } from "./persistedText";

/**
 * This install's device ID, sent with every sign-in (user, 2026-10-19): the server lets a person be
 * signed in on a limited number of devices and needs to tell them apart - signing in again on the
 * same phone replaces that phone's own session instead of taking another place. Made once, kept in
 * a file like the company and the server URL; not a secret, and not tied to the person.
 */
const store = persistedText("device-id.txt");

function newId(): string {
  const random = () => Math.random().toString(36).slice(2, 10);
  return `${Date.now().toString(36)}-${random()}-${random()}`;
}

let current: string | null = store.read();

export function getDeviceId(): string {
  if (!current) {
    current = newId();
    store.write(current);
  }
  return current;
}

/** A name to show for this device in a list of signed-in devices, e.g. "SM-A515F (Android)". */
export function getDeviceName(): string {
  const system = Platform.OS === "ios" ? "iOS" : Platform.OS === "android" ? "Android" : Platform.OS;
  return Device.modelName ? `${Device.modelName} (${system})` : system;
}

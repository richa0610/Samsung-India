import { useState } from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { Ionicons } from "@expo/vector-icons";

import AppInput from "@/components/ui/AppInput";
import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { OutsideVenuePrompt } from "./useSessionDashboardScreen";

type OutsideVenueModalProps = {
  prompt: OutsideVenuePrompt | null;
  onCancel: () => void;
  onSave: (latitude: number, longitude: number) => void;
};

const coord = (v: string) => {
  const n = Number(v.trim());
  return Number.isFinite(n) ? n : null;
};

export default function OutsideVenueModal({ prompt, onCancel, onSave }: OutsideVenueModalProps) {
  const [editing, setEditing] = useState(false);
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");

  // Reset the form each time a new prompt opens / it closes - done during
  // render (React's "adjust state on prop change" pattern), not in an effect.
  const [seenPrompt, setSeenPrompt] = useState(prompt);
  if (prompt !== seenPrompt) {
    setSeenPrompt(prompt);
    setEditing(false);
    setLat("");
    setLng("");
  }

  const useMyLocation = () => {
    if (!prompt?.trainerCoords) return;
    setLat(String(prompt.trainerCoords.latitude));
    setLng(String(prompt.trainerCoords.longitude));
  };

  const save = () => {
    const la = coord(lat);
    const ln = coord(lng);
    if (la === null || ln === null || Math.abs(la) > 90 || Math.abs(ln) > 180) return;
    onSave(la, ln);
  };

  const locked = prompt?.locked ?? false;

  return (
    <AppModal visible={!!prompt} onClose={onCancel} position="center" contentStyle={styles.sheet}>
      <View style={styles.header}>
        <Ionicons name="location" size={18} color="#F59E0B" />
        <AppText style={styles.title}>You&apos;re not at the venue</AppText>
      </View>
      {locked ? (
        <AppText style={styles.body}>
          You&apos;re about {prompt?.distanceMeters} m from the venue (allowed: {prompt?.radius} m).
          This venue&apos;s location was already confirmed once and can&apos;t be corrected again —
          start the session from the venue.
        </AppText>
      ) : (
        <AppText style={styles.body}>
          You&apos;re about {prompt?.distanceMeters} m from the saved venue location (allowed:{" "}
          {prompt?.radius} m). The venue location may be wrong — update it? This can only be done
          once for this venue.
        </AppText>
      )}

      {locked ? (
        <View style={styles.actionsRow}>
          <Pressable onPress={onCancel} hitSlop={8}>
            <AppText style={styles.primaryText}>OK</AppText>
          </Pressable>
        </View>
      ) : !editing ? (
        <View style={styles.actionsRow}>
          <Pressable onPress={onCancel} hitSlop={8}>
            <AppText style={styles.secondaryText}>No</AppText>
          </Pressable>
          <Pressable onPress={() => setEditing(true)} hitSlop={8}>
            <AppText style={styles.primaryText}>Yes, update</AppText>
          </Pressable>
        </View>
      ) : (
        <>
          <AppInput compact label="Latitude" value={lat} onChangeText={setLat} keyboardType="numbers-and-punctuation" placeholder="e.g. 28.5721" />
          <AppInput compact label="Longitude" value={lng} onChangeText={setLng} keyboardType="numbers-and-punctuation" placeholder="e.g. 77.3210" />
          {prompt?.trainerCoords && (
            <Pressable style={styles.useLocation} onPress={useMyLocation} hitSlop={6}>
              <Ionicons name="navigate" size={13} color="#2563EB" />
              <AppText style={styles.useLocationText}>Use my current location</AppText>
            </Pressable>
          )}
          <View style={styles.actionsRow}>
            <Pressable onPress={onCancel} hitSlop={8}>
              <AppText style={styles.secondaryText}>Cancel</AppText>
            </Pressable>
            <Pressable onPress={save} disabled={coord(lat) === null || coord(lng) === null} hitSlop={8}>
              <AppText style={[styles.primaryText, (coord(lat) === null || coord(lng) === null) && styles.disabled]}>
                Save &amp; start
              </AppText>
            </Pressable>
          </View>
        </>
      )}
    </AppModal>
  );
}

const styles = StyleSheet.create({
  sheet: { backgroundColor: "#1F2530", borderRadius: 12, padding: 18, width: "88%" },
  header: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 10 },
  title: { flex: 1, fontSize: 15, fontWeight: "800", color: "#F3F4F6" },
  body: { fontSize: 12, color: "#D1D5DB", lineHeight: 18, marginBottom: 16 },
  actionsRow: { flexDirection: "row", justifyContent: "flex-end", gap: 22, marginTop: 16 },
  secondaryText: { fontSize: 13, color: "#9CA3AF", fontWeight: "600" },
  primaryText: { fontSize: 13, color: "#60A5FA", fontWeight: "800" },
  disabled: { opacity: 0.4 },
  useLocation: { flexDirection: "row", alignItems: "center", gap: 6, marginTop: 8 },
  useLocationText: { fontSize: 12, color: "#60A5FA", fontWeight: "600" },
});

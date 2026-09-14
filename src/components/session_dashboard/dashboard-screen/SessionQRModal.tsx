import { useRef, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, View } from "react-native";
import * as Clipboard from "expo-clipboard";
import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";
import { Ionicons } from "@expo/vector-icons";
import QRCode from "react-native-qrcode-svg";

import AppModal from "@/components/ui/AppModal";
import AppText from "@/components/ui/AppText";
import { Colors } from "@/theme/colors";
import { FontWeight } from "@/theme/fontWeight";

type SessionQRModalProps = {
  visible: boolean;
  onClose: () => void;
  conferenceUid: string;
};

// Deep link the OS routes to this app (see `scheme` in app.json). Scanning
// it with a phone camera / Google Lens opens the app straight on the join
// screen; the same string works as a tappable link shared over chat.
const joinLink = (code: string) => `samsungindia://join/${code}`;

export default function SessionQRModal({ visible, onClose, conferenceUid }: SessionQRModalProps) {
  const [copied, setCopied] = useState(false);
  const [sharing, setSharing] = useState(false);
  // react-native-qrcode-svg exposes toDataURL() on this ref.
  const qrRef = useRef<{ toDataURL: (cb: (base64: string) => void) => void } | null>(null);
  const link = joinLink(conferenceUid);

  const handleCopy = async () => {
    await Clipboard.setStringAsync(link);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  // Renders the QR to a PNG and hands it to the OS share sheet - so the
  // trainer can send it over WhatsApp, Telegram, email, Drive, Nearby Share,
  // etc. The recipient scans it live or via the app's "scan from gallery".
  const handleShare = () => {
    if (!qrRef.current || sharing) return;
    setSharing(true);
    qrRef.current.toDataURL(async (base64: string) => {
      try {
        const file = new File(Paths.cache, `session-qr-${conferenceUid}.png`);
        if (file.exists) file.delete();
        file.create();
        file.write(base64, { encoding: "base64" });
        if (await Sharing.isAvailableAsync()) {
          await Sharing.shareAsync(file.uri, {
            mimeType: "image/png",
            dialogTitle: `Session QR - ${conferenceUid}`,
            UTI: "public.png",
          });
        }
      } catch {
        // user cancelled or sharing unavailable - nothing to do
      } finally {
        setSharing(false);
      }
    });
  };

  return (
    <AppModal visible={visible} onClose={onClose} position="center" closeOnOverlayPress>
      <View style={styles.content}>
        <AppText style={styles.title} weight={FontWeight.bold}>
          Session QR Code
        </AppText>
        <AppText style={styles.subtitle}>
          Trainees scan this to join {conferenceUid}
        </AppText>

        <View style={styles.qrBox}>
          {/* quietZone = the mandatory white border around a QR; without it
              scanners (esp. decoding a saved image) can't lock onto it. */}
          <QRCode
            value={link}
            size={230}
            quietZone={16}
            ecl="Q"
            getRef={(c) => (qrRef.current = c)}
          />
        </View>

        <Pressable
          style={[styles.shareBtn, sharing && styles.shareBtnDim]}
          onPress={handleShare}
          disabled={sharing}
        >
          {sharing ? (
            <ActivityIndicator size="small" color={Colors.white} />
          ) : (
            <>
              <Ionicons name="share-social" size={15} color={Colors.white} />
              <AppText style={styles.shareText} weight={FontWeight.bold}>Share QR</AppText>
            </>
          )}
        </Pressable>

        <Pressable style={styles.copyBtn} onPress={handleCopy} hitSlop={6}>
          <Ionicons
            name={copied ? "checkmark" : "copy-outline"}
            size={14}
            color={Colors.mainColour1}
          />
          <AppText style={styles.copyText} weight={FontWeight.medium}>
            {copied ? "Link copied" : "Copy join link"}
          </AppText>
        </Pressable>
      </View>
    </AppModal>
  );
}

const styles = StyleSheet.create({
  content: {
    backgroundColor: Colors.white,
    borderRadius: 20,
    padding: 20,
    alignItems: "center",
    width: "90%",
    maxWidth: 360,
    alignSelf: "center",
  },
  title: { fontSize: 16, color: "#111827", marginBottom: 4 },
  subtitle: { fontSize: 11, color: "#6B7280", marginBottom: 16, textAlign: "center" },
  qrBox: {
    padding: 12,
    backgroundColor: Colors.white,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
  },
  shareBtn: {
    marginTop: 18,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: Colors.mainColour1,
    borderRadius: 12,
    paddingVertical: 11,
    paddingHorizontal: 22,
    minWidth: 160,
  },
  shareBtnDim: { opacity: 0.6 },
  shareText: { fontSize: 13.5, color: Colors.white },
  copyBtn: {
    marginTop: 6,
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  copyText: { fontSize: 12, color: Colors.mainColour1 },
});

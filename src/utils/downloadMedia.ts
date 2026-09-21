import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";

/** Downloads a remote file into the app cache and opens the OS share sheet so
 *  it can be saved to the device / Drive / sent on. */
export async function downloadAndShare(url: string, fileName: string): Promise<void> {
  const safeName = fileName.replace(/[^a-z0-9._-]+/gi, "_");
  const destination = new File(Paths.cache, safeName);
  if (destination.exists) destination.delete();
  const file = await File.downloadFileAsync(url, destination);
  if (await Sharing.isAvailableAsync()) {
    await Sharing.shareAsync(file.uri, { dialogTitle: fileName });
  }
}

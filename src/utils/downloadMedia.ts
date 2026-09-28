import { File, Paths } from "expo-file-system";
import * as Print from "expo-print";

const IMAGE_EXTENSION_MIME: Record<string, string> = {
  jpg: "image/jpeg",
  jpeg: "image/jpeg",
  png: "image/png",
  webp: "image/webp",
  gif: "image/gif",
};

/** Downloads a remote file into the app cache and opens the native print
 *  dialog for it - "Download" is meant to let the trainer/admin save the
 *  file to their device, and the print sheet's own "Save as PDF" option
 *  covers that without needing a share-sheet round trip through another app.
 *  `headers` is required for anything under /media - that route is
 *  auth-gated (see backend/app/routers/media.py), and a plain
 *  unauthenticated download 401s.
 *
 *  Print.printAsync's `uri` option only accepts PDFs, not images - an image
 *  is instead embedded as base64 inside a one-image HTML page and printed
 *  via the `html` option. */
export async function downloadAndPrint(
  url: string,
  fileName: string,
  headers?: Record<string, string>,
): Promise<void> {
  const safeName = fileName.replace(/[^a-z0-9._-]+/gi, "_");
  const destination = new File(Paths.cache, safeName);
  if (destination.exists) destination.delete();
  const file = await File.downloadFileAsync(url, destination, headers ? { headers } : undefined);

  const extension = safeName.split(".").pop()?.toLowerCase() ?? "";
  const imageMime = IMAGE_EXTENSION_MIME[extension];

  if (imageMime) {
    const base64 = await file.base64();
    await Print.printAsync({
      html: `<html><body style="margin:0"><img src="data:${imageMime};base64,${base64}" style="width:100%" /></body></html>`,
    });
  } else {
    await Print.printAsync({ uri: file.uri });
  }
}

import { File, Paths } from "expo-file-system";

/**
 * A small text value kept in a file in the app's documents folder (expo-file-system, already
 * bundled) - for settings that must be known synchronously at module load, before the first
 * request (the server URL, the company). Every failure is swallowed: a value that can't be read is
 * simply absent, and one that can't be written still applies in memory for this session.
 */
export type PersistedText = {
  read(): string | null;
  write(value: string): void;
  remove(): void;
};

export function persistedText(fileName: string): PersistedText {
  const file = (): File | null => {
    try {
      return new File(Paths.document, fileName);
    } catch {
      return null;
    }
  };

  return {
    read() {
      try {
        const f = file();
        const value = f?.exists ? f.textSync().trim() : "";
        return value || null;
      } catch {
        return null;
      }
    },
    write(value) {
      try {
        const f = file();
        if (!f) return;
        if (!f.exists) f.create();
        f.write(value);
      } catch {
        // the in-memory value still applies for this session
      }
    },
    remove() {
      try {
        const f = file();
        if (f?.exists) f.delete();
      } catch {
        // nothing stored, or it can't be reached - either way it isn't read back
      }
    },
  };
}

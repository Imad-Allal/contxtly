import { useState, useRef } from "react";
import { exportToAnki } from "../chrome-api";
import type { Word } from "../types";
import { getWordKey } from "./useWords";

export function useAnkiExport() {
  const [ankiStatus, setAnkiStatus] = useState<{ msg: string; error: boolean } | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  const handleExport = async (words: Word[]) => {
    setIsExporting(true);
    clearTimeout(timerRef.current);
    try {
      const keys = words.map(getWordKey);
      const status = await exportToAnki(keys);
      setAnkiStatus(status);
    } catch {
      setAnkiStatus({ msg: "Anki not running. Open Anki with AnkiConnect.", error: true });
    } finally {
      setIsExporting(false);
      timerRef.current = setTimeout(() => setAnkiStatus(null), 4500);
    }
  };

  return { ankiStatus, isExporting, handleExport };
}

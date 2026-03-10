import { useState, useRef } from "react";
import { exportToAnki } from "../chrome-api";

export function useAnkiExport() {
  const [ankiStatus, setAnkiStatus] = useState<{ msg: string; error: boolean } | null>(null);
  const [isExporting, setIsExporting] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout>>();

  const handleExport = async () => {
    setIsExporting(true);
    clearTimeout(timerRef.current);
    try {
      const status = await exportToAnki();
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

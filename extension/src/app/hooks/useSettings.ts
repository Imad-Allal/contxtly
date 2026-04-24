import { useState, useEffect } from "react";
import { loadSettings, saveSettings } from "../chrome-api";

export function useSettings() {
  const [targetLang, setTargetLang] = useState("en");
  const [mode, setMode] = useState("smart");
  const [enabled, setEnabled] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    loadSettings().then((s) => {
      if (s?.targetLang) setTargetLang(s.targetLang);
      if (s?.mode) setMode(s.mode);
      if (typeof s?.enabled === "boolean") setEnabled(s.enabled);
    });
  }, []);

  const handleLangChange = (lang: string) => {
    setTargetLang(lang);
    saveSettings({ targetLang: lang, mode, enabled });
  };

  const handleModeChange = (m: string) => {
    setMode(m);
    saveSettings({ targetLang, mode: m, enabled });
  };

  const handleEnabledChange = (v: boolean) => {
    setEnabled(v);
    saveSettings({ targetLang, mode, enabled: v });
  };

  const toggleSettings = () => setSettingsOpen((v) => !v);

  return {
    targetLang,
    mode,
    enabled,
    settingsOpen,
    handleLangChange,
    handleModeChange,
    handleEnabledChange,
    toggleSettings,
  };
}

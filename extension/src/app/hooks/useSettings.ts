import { useState, useEffect } from "react";
import { loadSettings, saveSettings } from "../chrome-api";

export function useSettings() {
  const [targetLang, setTargetLang] = useState("en");
  const [mode, setMode] = useState("smart");
  const [settingsOpen, setSettingsOpen] = useState(false);

  useEffect(() => {
    loadSettings().then((s) => {
      if (s?.targetLang) setTargetLang(s.targetLang);
      if (s?.mode) setMode(s.mode);
    });
  }, []);

  const handleLangChange = (lang: string) => {
    setTargetLang(lang);
    saveSettings({ targetLang: lang, mode });
  };

  const handleModeChange = (m: string) => {
    setMode(m);
    saveSettings({ targetLang, mode: m });
  };

  const toggleSettings = () => setSettingsOpen((v) => !v);

  return { targetLang, mode, settingsOpen, handleLangChange, handleModeChange, toggleSettings };
}

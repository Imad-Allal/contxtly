import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Languages, LogIn } from "lucide-react";
import { deleteWords, getWordsFromDB, deleteWordFromDB, openUrl } from "./chrome-api";
import { useSettings } from "./hooks/useSettings";
import { useAnkiExport } from "./hooks/useAnkiExport";
import { useAuth } from "./hooks/useAuth";
import { useWordSelection, useWordFilter, useExpandedWords, getWordKey } from "./hooks/useWords";
import { BackgroundOrbs } from "./components/BackgroundOrbs";
import { Header } from "./components/Header";
import { SettingsPanel } from "./components/SettingsPanel";
import { Toolbar } from "./components/Toolbar";
import { WordCard } from "./components/WordCard";
import { EmptyState } from "./components/EmptyState";
import { Footer } from "./components/Footer";
import type { Word } from "./types";

export default function App() {
  const [words, setWords] = useState<Word[]>([]);
  const [search, setSearch] = useState("");

  const settings = useSettings();
  const { ankiStatus, isExporting, handleExport } = useAnkiExport();
  const auth = useAuth();
  const filtered = useWordFilter(words, search);
  const { selected, allSelected, toggleSelect, toggleSelectAll, clearSelection } = useWordSelection(filtered);
  const { expandedWords, toggleExpand } = useExpandedWords();

  // Show cached DB words instantly, then refresh from DB in background
  useEffect(() => {
    if (auth.loading || !auth.loggedIn) return;

    // 1. Show cached words immediately
    chrome.storage.local.get("words_cache", (result) => {
      const cached = result.words_cache as Word[] | undefined;
      if (cached && cached.length > 0) setWords(cached);
    });

    // 2. Refresh from DB silently
    getWordsFromDB().then((dbWords) => {
      setWords(dbWords);
      chrome.storage.local.set({ words_cache: dbWords });
    });
  }, [auth.loggedIn, auth.loading]);

  const handleDelete = useCallback(async () => {
    const selected_words = words.filter((w) => selected.has(getWordKey(w)));
    const lemmas = selected_words.map(getWordKey);

    // Delete from local storage + DOM highlights
    await deleteWords(lemmas);

    // Delete from DB if logged in (use row id)
    if (auth.loggedIn) {
      await Promise.all(
        selected_words
          .filter((w) => (w as Word & { id?: string }).id)
          .map((w) => deleteWordFromDB((w as Word & { id?: string }).id!))
      );
    }

    setWords((prev) => prev.filter((w) => !lemmas.includes(getWordKey(w))));
    clearSelection();
  }, [words, selected, auth.loggedIn, clearSelection]);

  const handleOpenUrl = useCallback((url: string) => openUrl(url), []);

  if (!auth.loading && !auth.loggedIn) {
    return (
      <div
        className="relative w-[380px] flex flex-col items-center justify-center overflow-hidden"
        style={{
          height: "560px",
          background: "linear-gradient(135deg, #f8fafc 0%, rgba(219,234,254,0.25) 50%, rgba(237,233,254,0.25) 100%)",
          fontFamily: "'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif",
        }}
      >
        <BackgroundOrbs />
        <div className="relative z-10 flex flex-col items-center gap-6 px-8 text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-xl"
            style={{ background: "linear-gradient(135deg, #4f46e5, #6366f1)", boxShadow: "0 8px 24px rgba(99,102,241,0.3)" }}
          >
            <Languages className="text-white" size={32} />
          </motion.div>

          <motion.div
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1, duration: 0.3 }}
          >
            <h1 className="text-xl font-extrabold text-slate-800">Welcome to Contxtly</h1>
            <p className="text-sm text-slate-500 mt-1">Sign in to start translating and saving words across the web.</p>
          </motion.div>

          <motion.button
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.3 }}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={auth.login}
            className="flex items-center gap-2.5 px-6 py-3 rounded-xl text-white font-bold text-sm shadow-lg"
            style={{ background: "linear-gradient(135deg, #4f46e5, #6366f1)", boxShadow: "0 4px 16px rgba(99,102,241,0.35)" }}
          >
            <LogIn size={16} />
            Sign in with Google
          </motion.button>
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative w-[380px] flex flex-col overflow-hidden"
      style={{
        height: "560px",
        background: "linear-gradient(135deg, #f8fafc 0%, rgba(219,234,254,0.25) 50%, rgba(237,233,254,0.25) 100%)",
        fontFamily: "'Plus Jakarta Sans', ui-sans-serif, system-ui, sans-serif",
      }}
    >
      <BackgroundOrbs />

      <div className="relative z-10 flex flex-col h-full">
        <Header
          settingsOpen={settings.settingsOpen}
          onToggleSettings={settings.toggleSettings}
          auth={auth}
          onLogin={auth.login}
          onLogout={auth.logout}
        />

        <SettingsPanel
          open={settings.settingsOpen}
          targetLang={settings.targetLang}
          mode={settings.mode}
          onLangChange={settings.handleLangChange}
          onModeChange={settings.handleModeChange}
          auth={auth}
        />

        <Toolbar
          search={search}
          onSearchChange={setSearch}
          isExporting={isExporting}
          onExport={handleExport}
          allSelected={allSelected}
          onToggleSelectAll={toggleSelectAll}
          selectedCount={selected.size}
          onDelete={handleDelete}
        />

        <div className="flex-1 overflow-y-auto px-3 py-2.5 space-y-1.5 custom-scroll">
          {filtered.length === 0 ? (
            <EmptyState isSearch={!!search} />
          ) : (
            filtered.map((word, index) => (
              <WordCard
                key={getWordKey(word)}
                word={word}
                index={index}
                isSelected={selected.has(getWordKey(word))}
                isExpanded={expandedWords.has(getWordKey(word))}
                onToggleSelect={toggleSelect}
                onToggleExpand={toggleExpand}
                onOpenUrl={handleOpenUrl}
              />
            ))
          )}
        </div>

        <Footer wordCount={filtered.length} ankiStatus={ankiStatus} />
      </div>
    </div>
  );
}

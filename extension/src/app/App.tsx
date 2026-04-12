import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Languages, LogIn, Trash2, ArrowLeft, Undo2 } from "lucide-react";
import {
  loadWords, deleteWords, deleteWordFromDB,
  getWordsFromDB, syncDBWordsToHighlights,
  getTrash, restoreWords, purgeWords,
  openUrl,
} from "./chrome-api";
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
  const [trashWords, setTrashWords] = useState<Word[]>([]);
  const [showTrash, setShowTrash] = useState(false);

  const settings = useSettings();
  const { ankiStatus, isExporting, handleExport } = useAnkiExport();
  const auth = useAuth();

  // Main list state
  const filtered = useWordFilter(words, search);
  const { selected, allSelected, toggleSelect, toggleSelectAll, clearSelection } = useWordSelection(filtered);
  const { expandedWords, toggleExpand } = useExpandedWords();

  // Trash list state (reuse same hooks on trashWords)
  const filteredTrash = useWordFilter(trashWords, "");
  const { selected: trashSelected, allSelected: allTrashSelected, toggleSelect: toggleTrashSelect, toggleSelectAll: toggleTrashSelectAll, clearSelection: clearTrashSelection } = useWordSelection(filteredTrash);
  const { expandedWords: trashExpanded, toggleExpand: toggleTrashExpand } = useExpandedWords();

  // Load words: browser storage first (instant), then attach DB ids in background
  useEffect(() => {
    if (auth.loading || !auth.loggedIn) return;

    async function loadAndSync() {
      const browserWords = await loadWords();

      if (browserWords.length > 0) {
        // Show browser words immediately, then fetch DB ids to attach
        setWords(browserWords);
        const dbWords = await getWordsFromDB();
        const idByText = new Map(dbWords.map((w) => [w.text, w.id]));
        setWords((prev) =>
          prev.map((w) => ({ ...w, id: w.id ?? idByText.get(w.text) }))
        );
      } else {
        // Browser empty — fetch from DB, store locally, then display
        const dbWords = await getWordsFromDB();
        if (dbWords.length > 0) {
          await syncDBWordsToHighlights(dbWords);
          const synced = await loadWords();
          // DB words already have ids
          const idByText = new Map(dbWords.map((w) => [w.text, w.id]));
          setWords(synced.map((w) => ({ ...w, id: w.id ?? idByText.get(w.text) })));
        }
      }
    }

    loadAndSync();
  }, [auth.loggedIn, auth.loading]);

  // Load trash when panel opens
  useEffect(() => {
    if (!showTrash || !auth.loggedIn) return;
    getTrash().then(setTrashWords);
  }, [showTrash, auth.loggedIn]);

  const handleDelete = useCallback(async () => {
    const selected_words = words.filter((w) => selected.has(getWordKey(w)));
    const lemmas = selected_words.map(getWordKey);

    await deleteWords(lemmas);

    if (auth.loggedIn) {
      await Promise.all(
        selected_words.filter((w) => w.id).map((w) => deleteWordFromDB(w.id!))
      );
    }

    setWords((prev) => prev.filter((w) => !lemmas.includes(getWordKey(w))));
    clearSelection();
  }, [words, selected, auth.loggedIn, clearSelection]);

  const handleRestore = useCallback(async () => {
    const ids = trashWords
      .filter((w) => trashSelected.has(getWordKey(w)) && w.id)
      .map((w) => w.id!);
    if (ids.length === 0) return;

    const restored = await restoreWords(ids);

    // Write restored words into local highlights so they appear immediately
    if (restored.length > 0) {
      await syncDBWordsToHighlights(restored);
      const updatedWords = await loadWords();
      setWords(updatedWords);
    }

    // Refresh trash list
    const updatedTrash = await getTrash();
    setTrashWords(updatedTrash);
    clearTrashSelection();
  }, [trashWords, trashSelected, clearTrashSelection]);

  const handlePermanentDelete = useCallback(async () => {
    const ids = trashWords
      .filter((w) => trashSelected.has(getWordKey(w)) && w.id)
      .map((w) => w.id!);
    if (ids.length === 0) return;

    await purgeWords(ids);
    const updatedTrash = await getTrash();
    setTrashWords(updatedTrash);
    clearTrashSelection();
  }, [trashWords, trashSelected, clearTrashSelection]);

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
        <AnimatePresence mode="wait">
          {showTrash ? (
            // ── Trash view ──────────────────────────────────────────────────
            <motion.div
              key="trash"
              initial={{ x: 380 }}
              animate={{ x: 0 }}
              exit={{ x: 380 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="flex flex-col h-full"
            >
              {/* Trash header */}
              <div
                className="flex items-center gap-2 px-3 py-2.5 border-b border-slate-100/80"
                style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)" }}
              >
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => { setShowTrash(false); clearTrashSelection(); }}
                  className="w-8 h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-slate-500 hover:bg-slate-50 transition-all"
                >
                  <ArrowLeft size={14} />
                </motion.button>
                <span className="flex-1 text-[13px] font-bold text-slate-700 flex items-center gap-1.5">
                  <Trash2 size={13} className="text-slate-400" />
                  Trash
                  {trashWords.length > 0 && (
                    <span className="text-[11px] font-semibold text-slate-400">({trashWords.length}/10)</span>
                  )}
                </span>
                {/* Trash toolbar: select all + restore */}
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={toggleTrashSelectAll}
                  title={allTrashSelected ? "Deselect all" : "Select all"}
                  className={`w-8 h-8 rounded-lg flex items-center justify-center border transition-all text-[11px] font-bold ${
                    allTrashSelected
                      ? "bg-indigo-50 border-indigo-200 text-indigo-600"
                      : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                  }`}
                >
                  {allTrashSelected ? "✓" : "○"}
                </motion.button>
                <AnimatePresence>
                  {trashSelected.size > 0 && (
                    <>
                      <motion.button
                        initial={{ opacity: 0, scale: 0.7, width: 0 }}
                        animate={{ opacity: 1, scale: 1, width: 32 }}
                        exit={{ opacity: 0, scale: 0.7, width: 0 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleRestore}
                        title={`Restore ${trashSelected.size} selected`}
                        className="relative h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-amber-500 hover:bg-amber-50 hover:border-amber-200 transition-all overflow-visible flex-shrink-0"
                      >
                        <Undo2 size={13} />
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-1.5 -right-1.5 w-[15px] h-[15px] rounded-full bg-amber-400 text-white text-[9px] font-bold flex items-center justify-center border border-white"
                        >
                          {trashSelected.size}
                        </motion.span>
                      </motion.button>
                      <motion.button
                        initial={{ opacity: 0, scale: 0.7, width: 0 }}
                        animate={{ opacity: 1, scale: 1, width: 32 }}
                        exit={{ opacity: 0, scale: 0.7, width: 0 }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handlePermanentDelete}
                        title={`Permanently delete ${trashSelected.size} selected`}
                        className="relative h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-red-400 hover:bg-red-50 hover:border-red-200 transition-all overflow-visible flex-shrink-0"
                      >
                        <Trash2 size={13} />
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-1.5 -right-1.5 w-[15px] h-[15px] rounded-full bg-red-400 text-white text-[9px] font-bold flex items-center justify-center border border-white"
                        >
                          {trashSelected.size}
                        </motion.span>
                      </motion.button>
                    </>
                  )}
                </AnimatePresence>
              </div>

              {/* Trash word list */}
              <div className="flex-1 overflow-y-auto px-3 py-2.5 space-y-1.5 custom-scroll">
                {filteredTrash.length === 0 ? (
                  <EmptyState isSearch={false} />
                ) : (
                  filteredTrash.map((word, index) => (
                    <WordCard
                      key={getWordKey(word)}
                      word={word}
                      index={index}
                      isSelected={trashSelected.has(getWordKey(word))}
                      isExpanded={trashExpanded.has(getWordKey(word))}
                      onToggleSelect={toggleTrashSelect}
                      onToggleExpand={toggleTrashExpand}
                      onOpenUrl={handleOpenUrl}
                    />
                  ))
                )}
              </div>

              <Footer wordCount={filteredTrash.length} ankiStatus={null} />
            </motion.div>
          ) : (
            // ── Main view ───────────────────────────────────────────────────
            <motion.div
              key="main"
              initial={{ x: -380 }}
              animate={{ x: 0 }}
              exit={{ x: -380 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="flex flex-col h-full"
            >
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
                onOpenTrash={() => setShowTrash(true)}
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

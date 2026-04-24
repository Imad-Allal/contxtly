import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { LogIn, Trash2, ArrowLeft, Undo2 } from "lucide-react";
import { ContxtlyLogo } from "./ContxtlyLogo";
import { useReducedMotion } from "./hooks/useReducedMotion";
import {
  loadWords, loadArchives,
  archiveWords, restoreWords, purgeWords,
  syncFromDBIfEmpty,
  openUrl,
} from "./chrome-api";
import { useSettings } from "./hooks/useSettings";
import { useAnkiExport } from "./hooks/useAnkiExport";
import { useAuth } from "./hooks/useAuth";
import { useWordSelection, useWordFilter, useExpandedWords, getWordKey, type WordTypeFilter } from "./hooks/useWords";
import { useOnboarding } from "./hooks/useOnboarding";
import { useShortcuts } from "./hooks/useShortcuts";
import { BackgroundOrbs } from "./components/BackgroundOrbs";
import { Header, type AppTab } from "./components/Header";
import { SettingsPanel } from "./components/SettingsPanel";
import { Toolbar } from "./components/Toolbar";
import { WordCard } from "./components/WordCard";
import { EmptyState } from "./components/EmptyState";
import { Footer } from "./components/Footer";
import { OnboardingOverlay } from "./components/onboarding/OnboardingOverlay";
import { ShortcutsOverlay } from "./components/ShortcutsOverlay";
import { WordOfDay } from "./components/WordOfDay";
import { StatsPanel } from "./components/StatsPanel";
import { ReviewView } from "./components/ReviewView";
import { BG_GRADIENT, FONT_STACK, PRIMARY_GRADIENT } from "./theme";
import type { Word } from "./types";

export default function App() {
  const [words, setWords] = useState<Word[]>([]);
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<WordTypeFilter>("all");
  const [trashWords, setTrashWords] = useState<Word[]>([]);
  const [showTrash, setShowTrash] = useState(false);
  const [tab, setTab] = useState<AppTab>("list");
  const [showShortcuts, setShowShortcuts] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);

  const settings = useSettings();
  const anki = useAnkiExport();
  const auth = useAuth();
  const onboarding = useOnboarding(auth.loggedIn);
  const reduced = useReducedMotion();

  const filtered = useWordFilter(words, search, typeFilter);
  const { selected, allSelected, toggleSelect, toggleSelectAll, clearSelection } = useWordSelection(filtered);
  const { expandedWords, toggleExpand } = useExpandedWords();

  const filteredTrash = useWordFilter(trashWords, "");
  const { selected: trashSelected, allSelected: allTrashSelected, toggleSelect: toggleTrashSelect, toggleSelectAll: toggleTrashSelectAll, clearSelection: clearTrashSelection } = useWordSelection(filteredTrash);
  const { expandedWords: trashExpanded, toggleExpand: toggleTrashExpand } = useExpandedWords();

  useEffect(() => {
    if (auth.loading || !auth.loggedIn) return;
    loadWords().then(setWords);
    syncFromDBIfEmpty().then(() => loadWords().then(setWords));
  }, [auth.loggedIn, auth.loading]);

  useEffect(() => {
    if (!showTrash || !auth.loggedIn) return;
    loadArchives().then(setTrashWords);
  }, [showTrash, auth.loggedIn]);

  useEffect(() => {
    if (!auth.loggedIn) return;
    const listener = (changes: Record<string, chrome.storage.StorageChange>) => {
      if (changes.words) setWords((changes.words.newValue as Word[]) || []);
      if (changes.archives && showTrash) setTrashWords((changes.archives.newValue as Word[]) || []);
    };
    chrome.storage.onChanged.addListener(listener);
    return () => chrome.storage.onChanged.removeListener(listener);
  }, [auth.loggedIn, showTrash]);

  useShortcuts({
    onFocusSearch: () => searchInputRef.current?.focus(),
    onToggleTrash: () => setShowTrash((v) => !v),
    onListTab: () => setTab("list"),
    onReviewTab: () => setTab("review"),
    onStatsTab: () => setTab("stats"),
    onExport: () => anki.handleExport(words.filter((w) => selected.has(getWordKey(w))).length > 0 ? words.filter((w) => selected.has(getWordKey(w))) : words),
    onHelp: () => setShowShortcuts(true),
    onEscape: () => {
      if (showShortcuts) setShowShortcuts(false);
      else if (showTrash) setShowTrash(false);
    },
  }, auth.loggedIn && !onboarding.showOverlay);

  const handleDelete = useCallback(async () => {
    const lemmas = words.filter((w) => selected.has(getWordKey(w))).map(getWordKey);
    await archiveWords(lemmas);
    setWords((prev) => prev.filter((w) => !lemmas.includes(getWordKey(w))));
    clearSelection();
  }, [words, selected, clearSelection]);

  const handleRestore = useCallback(async () => {
    const lemmas = trashWords.filter((w) => trashSelected.has(getWordKey(w))).map(getWordKey);
    if (lemmas.length === 0) return;
    await restoreWords(lemmas);
    setTrashWords((prev) => prev.filter((w) => !lemmas.includes(getWordKey(w))));
    setWords(await loadWords());
    clearTrashSelection();
  }, [trashWords, trashSelected, clearTrashSelection]);

  const handlePermanentDelete = useCallback(async () => {
    const lemmas = trashWords.filter((w) => trashSelected.has(getWordKey(w))).map(getWordKey);
    if (lemmas.length === 0) return;
    await purgeWords(lemmas);
    setTrashWords((prev) => prev.filter((w) => !lemmas.includes(getWordKey(w))));
    clearTrashSelection();
  }, [trashWords, trashSelected, clearTrashSelection]);

  const handleOpenUrl = useCallback((url: string) => openUrl(url), []);

  const handleOpenWord = useCallback((w: Word) => {
    setTab("list");
    const key = getWordKey(w);
    if (!expandedWords.has(key)) toggleExpand(key);
    requestAnimationFrame(() => {
      setTimeout(() => {
        const el = document.querySelector(`[data-word-key="${CSS.escape(key)}"]`);
        el?.scrollIntoView({ behavior: "smooth", block: "center" });
      }, 120);
    });
  }, [expandedWords, toggleExpand]);

  if (!auth.loading && !auth.loggedIn) {
    const containerStyle = {
      height: "560px",
      background: BG_GRADIENT,
      fontFamily: FONT_STACK,
    };

    if (auth.loggingIn) {
      return (
        <div className="relative w-[380px] flex flex-col items-center justify-center overflow-hidden" style={containerStyle}>
          <BackgroundOrbs />
          <div className="relative z-10 flex flex-col items-center gap-4 px-8 text-center">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1.2, repeat: Infinity, ease: "linear" }}
              className="w-10 h-10 rounded-full border-[3px] border-rose-200 border-t-rose-500"
            />
            <p className="text-sm font-semibold text-slate-500">Signing in...</p>
          </div>
        </div>
      );
    }

    return (
      <div className="relative w-[380px] flex flex-col items-center justify-center overflow-hidden" style={containerStyle}>
        <BackgroundOrbs />
        <div className="relative z-10 flex flex-col items-center gap-6 px-8 text-center">
          <motion.div
            initial={{ scale: 0.5, rotate: -8, opacity: 0 }}
            animate={{ scale: 1, rotate: 0, opacity: 1 }}
            transition={{ type: "spring", stiffness: 260, damping: 18 }}
            style={{ width: 72, height: 72 }}
          >
            <ContxtlyLogo size={72} reduced={reduced} />
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
            style={{ background: PRIMARY_GRADIENT, boxShadow: "0 4px 16px rgba(187,0,81,0.35)" }}
          >
            <LogIn size={16} />
            Sign in with Google
          </motion.button>
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3, duration: 0.3 }}
            className="text-[10.5px] text-slate-400 leading-relaxed max-w-[260px]"
          >
            By signing in, you agree to our{" "}
            <a
              href="https://legal.contxtly.xyz/terms.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-rose-600 hover:text-rose-700 underline underline-offset-2"
            >
              Terms
            </a>{" "}
            and{" "}
            <a
              href="https://legal.contxtly.xyz/privacy.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-rose-600 hover:text-rose-700 underline underline-offset-2"
            >
              Privacy Policy
            </a>
            .
          </motion.p>
        </div>
      </div>
    );
  }

  return (
    <div
      className="relative w-[380px] flex flex-col overflow-hidden"
      style={{
        height: "560px",
        background: BG_GRADIENT,
        fontFamily: FONT_STACK,
      }}
    >
      <BackgroundOrbs />

      <div className="relative z-10 flex flex-col h-full">
        <AnimatePresence mode="wait">
          {showTrash ? (
            <motion.div
              key="trash"
              initial={{ x: 380 }}
              animate={{ x: 0 }}
              exit={{ x: 380 }}
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
              className="flex flex-col h-full"
            >
              <div
                className="flex items-center gap-2 px-3 py-2.5 border-b border-slate-100/80"
                style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)" }}
              >
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => { setShowTrash(false); clearTrashSelection(); }}
                  aria-label="Back to list"
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
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={toggleTrashSelectAll}
                  aria-label={allTrashSelected ? "Deselect all" : "Select all"}
                  title={allTrashSelected ? "Deselect all" : "Select all"}
                  className={`w-8 h-8 rounded-lg flex items-center justify-center border transition-all text-[11px] font-bold ${
                    allTrashSelected
                      ? "bg-rose-50 border-rose-200 text-rose-600"
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
                        aria-label={`Restore ${trashSelected.size} selected`}
                        title={`Restore ${trashSelected.size} selected`}
                        className="relative h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-rose-500 hover:bg-rose-50 hover:border-rose-200 transition-all overflow-visible flex-shrink-0"
                      >
                        <Undo2 size={13} />
                        <motion.span
                          initial={{ scale: 0 }}
                          animate={{ scale: 1 }}
                          className="absolute -top-1.5 -right-1.5 w-[15px] h-[15px] rounded-full bg-rose-500 text-white text-[9px] font-bold flex items-center justify-center border border-white"
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
                        aria-label={`Permanently delete ${trashSelected.size} selected`}
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
                      autoExpandOnHover
                    />
                  ))
                )}
              </div>

              <Footer wordCount={filteredTrash.length} ankiStatus={null} />
            </motion.div>
          ) : (
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
                enabled={settings.enabled}
                onEnabledChange={settings.handleEnabledChange}
                auth={auth}
                onLogin={auth.login}
                onLogout={auth.logout}
                tab={tab}
                onTabChange={setTab}
              />

              <SettingsPanel
                open={settings.settingsOpen}
                targetLang={settings.targetLang}
                mode={settings.mode}
                onLangChange={settings.handleLangChange}
                onModeChange={settings.handleModeChange}
                auth={auth}
              />

              <AnimatePresence mode="wait">
                {tab === "list" && (
                  <motion.div
                    key="list"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                    className="flex flex-col flex-1 min-h-0"
                  >
                    <Toolbar
                      search={search}
                      onSearchChange={setSearch}
                      typeFilter={typeFilter}
                      onTypeFilterChange={setTypeFilter}
                      isExporting={anki.isExporting}
                      onExport={anki.handleExport}
                      selectedWords={words.filter((w) => selected.has(getWordKey(w)))}
                      allSelected={allSelected}
                      onToggleSelectAll={toggleSelectAll}
                      selectedCount={selected.size}
                      onDelete={handleDelete}
                      onOpenTrash={() => setShowTrash(true)}
                      searchInputRef={searchInputRef}
                      words={words}
                    />

                    <div className="flex-1 overflow-y-auto px-3 py-2.5 space-y-1.5 custom-scroll">
                      {filtered.length === 0 ? (
                        <EmptyState isSearch={!!search} />
                      ) : (
                        <>
                          {!search && typeFilter === "all" && words.length > 0 && (
                            <WordOfDay words={words} onOpen={handleOpenWord} />
                          )}
                          {filtered.map((word, index) => (
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
                          ))}
                        </>
                      )}
                    </div>
                  </motion.div>
                )}

                {tab === "review" && (
                  <motion.div
                    key="review"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                    className="flex flex-col flex-1 min-h-0"
                  >
                    <ReviewView words={words} />
                  </motion.div>
                )}

                {tab === "stats" && (
                  <motion.div
                    key="stats"
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.2 }}
                    className="flex flex-col flex-1 min-h-0"
                  >
                    <StatsPanel words={words} />
                  </motion.div>
                )}
              </AnimatePresence>

              <Footer wordCount={filtered.length} ankiStatus={anki.ankiStatus} />
            </motion.div>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {onboarding.showOverlay && (
            <OnboardingOverlay
              onFinish={onboarding.finish}
              targetLang={settings.targetLang}
              onLangChange={settings.handleLangChange}
            />
          )}
          {showShortcuts && !onboarding.showOverlay && (
            <ShortcutsOverlay onClose={() => setShowShortcuts(false)} />
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

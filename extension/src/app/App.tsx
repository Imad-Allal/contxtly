import { useState, useEffect, useCallback } from "react";
import { loadWords, deleteWords, openUrl } from "./chrome-api";
import { useSettings } from "./hooks/useSettings";
import { useAnkiExport } from "./hooks/useAnkiExport";
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
  const filtered = useWordFilter(words, search);
  const { selected, allSelected, toggleSelect, toggleSelectAll, clearSelection } = useWordSelection(filtered);
  const { expandedWords, toggleExpand } = useExpandedWords();

  useEffect(() => { loadWords().then(setWords); }, []);

  const handleDelete = useCallback(async () => {
    const lemmas = [...selected];
    await deleteWords(lemmas);
    setWords((prev) => prev.filter((w) => !lemmas.includes(getWordKey(w))));
    clearSelection();
  }, [selected, clearSelection]);

  const handleOpenUrl = useCallback((url: string) => openUrl(url), []);

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
        <Header settingsOpen={settings.settingsOpen} onToggleSettings={settings.toggleSettings} />

        <SettingsPanel
          open={settings.settingsOpen}
          targetLang={settings.targetLang}
          mode={settings.mode}
          onLangChange={settings.handleLangChange}
          onModeChange={settings.handleModeChange}
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

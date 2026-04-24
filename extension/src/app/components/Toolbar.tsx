import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Square, CheckSquare, Trash2, ArchiveX } from "lucide-react";
import type { RefObject } from "react";
import type { WordTypeFilter } from "../hooks/useWords";
import type { Word } from "../types";
import { COLORS, MOTION, RADIUS } from "../theme";
import { ExportMenu } from "./ExportMenu";

const TYPE_FILTERS: { value: WordTypeFilter; label: string; color: keyof typeof COLORS }[] = [
  { value: "all",         label: "All",     color: "slate" },
  { value: "noun",        label: "Noun",    color: "noun" },
  { value: "verb",        label: "Verb",    color: "verb" },
  { value: "collocation", label: "Colloc.", color: "collocation" },
  { value: "expression",  label: "Expr.",   color: "expression" },
  { value: "other",       label: "Other",   color: "compound" },
];

interface ToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  typeFilter: WordTypeFilter;
  onTypeFilterChange: (v: WordTypeFilter) => void;
  isExporting: boolean;
  onExport: (words: Word[]) => void;
  selectedWords: Word[];
  allSelected: boolean;
  onToggleSelectAll: () => void;
  selectedCount: number;
  onDelete: () => void;
  onOpenTrash: () => void;
  searchInputRef?: RefObject<HTMLInputElement>;
  words: Word[];
}

export function Toolbar({
  search, onSearchChange, typeFilter, onTypeFilterChange,
  isExporting, onExport, allSelected, onToggleSelectAll,
  selectedCount, onDelete, onOpenTrash, searchInputRef, words, selectedWords,
}: ToolbarProps) {
  return (
    <div
      className="relative flex flex-col border-b border-slate-100/80"
      style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)", zIndex: 20 }}
    >
      <div className="flex items-center gap-1.5 px-3 pt-2 pb-1.5 overflow-x-auto no-scrollbar">
        {TYPE_FILTERS.map((f) => {
          const swatch = COLORS[f.color];
          const active = typeFilter === f.value;
          return (
            <motion.button
              key={f.value}
              whileTap={{ scale: 0.95 }}
              onClick={() => onTypeFilterChange(f.value)}
              aria-pressed={active}
              className="flex-shrink-0 inline-flex items-center gap-1 px-2.5 py-1 text-[10.5px] font-semibold border transition-all"
              style={{
                borderRadius: RADIUS.pill,
                background: active ? swatch.bg : "#ffffff",
                borderColor: active ? swatch.ring : "#e2e8f0",
                color: active ? swatch.text : "#64748b",
              }}
            >
              {f.value !== "all" && (
                <span
                  className="inline-block w-1.5 h-1.5 rounded-full"
                  style={{ background: swatch.accent, opacity: active ? 1 : 0.65 }}
                />
              )}
              {f.label}
            </motion.button>
          );
        })}
      </div>

      <div className="flex items-center gap-1.5 px-3 pb-2">
      <div className="flex-1 relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={12} />
        <input
          ref={searchInputRef}
          type="text"
          placeholder="Search words..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          aria-label="Search saved words"
          className="w-full pl-7 pr-6 py-1.5 text-[12px] rounded-xl border border-slate-200 bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:border-rose-300 focus:ring-2 focus:ring-rose-100 transition-all font-medium"
        />
        <AnimatePresence>
          {search && (
            <motion.button
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.6 }}
              transition={MOTION.fast}
              onClick={() => onSearchChange("")}
              aria-label="Clear search"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X size={12} />
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      <ExportMenu words={words} selectedWords={selectedWords} isExporting={isExporting} onAnki={onExport} />

      <motion.button
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.94 }}
        onClick={onToggleSelectAll}
        aria-label={allSelected ? "Deselect all" : "Select all"}
        title={allSelected ? "Deselect all" : "Select all"}
        className={`w-8 h-8 rounded-xl flex items-center justify-center border transition-all ${
          allSelected
            ? "bg-rose-50 border-rose-200 text-rose-600"
            : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-700"
        }`}
      >
        {allSelected ? <CheckSquare size={14} /> : <Square size={14} />}
      </motion.button>

      <AnimatePresence mode="wait">
        {selectedCount > 0 ? (
          <motion.button
            key="delete"
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.7 }}
            transition={MOTION.fast}
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.94 }}
            onClick={onDelete}
            aria-label={`Delete ${selectedCount} selected`}
            title={`Delete ${selectedCount} selected`}
            className="relative w-8 h-8 rounded-xl flex items-center justify-center border border-slate-200 bg-white text-red-400 hover:bg-red-50 hover:border-red-200 hover:text-red-500 transition-all overflow-visible flex-shrink-0"
          >
            <Trash2 size={14} />
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={MOTION.spring}
              className="absolute -top-1.5 -right-1.5 w-[15px] h-[15px] rounded-full bg-red-400 text-white text-[9px] font-bold flex items-center justify-center border border-white"
            >
              {selectedCount}
            </motion.span>
          </motion.button>
        ) : (
          <motion.button
            key="archive"
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.7 }}
            transition={MOTION.fast}
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.94 }}
            onClick={onOpenTrash}
            aria-label="View trash"
            title="View trash"
            className="w-8 h-8 rounded-xl flex items-center justify-center border border-slate-200 bg-white text-slate-400 hover:bg-rose-50 hover:border-rose-200 hover:text-rose-500 transition-all"
          >
            <ArchiveX size={14} />
          </motion.button>
        )}
      </AnimatePresence>
      </div>
    </div>
  );
}

import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Layers, Square, CheckSquare, Trash2, ArchiveX } from "lucide-react";

interface ToolbarProps {
  search: string;
  onSearchChange: (value: string) => void;
  isExporting: boolean;
  onExport: () => void;
  allSelected: boolean;
  onToggleSelectAll: () => void;
  selectedCount: number;
  onDelete: () => void;
  onOpenTrash: () => void;
}

export function Toolbar({
  search, onSearchChange, isExporting, onExport,
  allSelected, onToggleSelectAll, selectedCount, onDelete,
  onOpenTrash,
}: ToolbarProps) {
  return (
    <div
      className="flex items-center gap-1.5 px-3 py-2 border-b border-slate-100/80"
      style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)" }}
    >
      {/* Search */}
      <div className="flex-1 relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" size={12} />
        <input
          type="text"
          placeholder="Search words..."
          value={search}
          onChange={(e) => onSearchChange(e.target.value)}
          className="w-full pl-7 pr-6 py-1.5 text-[12px] rounded-lg border border-slate-200 bg-white text-slate-700 placeholder-slate-400 focus:outline-none focus:border-slate-400 focus:ring-1 focus:ring-slate-200 transition-all font-medium"
        />
        <AnimatePresence>
          {search && (
            <motion.button
              initial={{ opacity: 0, scale: 0.6 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.6 }}
              transition={{ duration: 0.15 }}
              onClick={() => onSearchChange("")}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X size={12} />
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Anki export */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onExport}
        disabled={isExporting}
        title="Export to Anki"
        className="w-8 h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-emerald-600 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 transition-all disabled:opacity-40 disabled:cursor-not-allowed"
      >
        <motion.div
          animate={isExporting ? { rotate: 360 } : {}}
          transition={isExporting ? { duration: 0.9, repeat: Infinity, ease: "linear" } : {}}
        >
          <Layers size={14} />
        </motion.div>
      </motion.button>

      {/* Select all */}
      <motion.button
        whileHover={{ scale: 1.05 }}
        whileTap={{ scale: 0.95 }}
        onClick={onToggleSelectAll}
        title={allSelected ? "Deselect all" : "Select all"}
        className={`w-8 h-8 rounded-lg flex items-center justify-center border transition-all ${
          allSelected
            ? "bg-indigo-50 border-indigo-200 text-indigo-600"
            : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50 hover:text-slate-700"
        }`}
      >
        {allSelected ? <CheckSquare size={14} /> : <Square size={14} />}
      </motion.button>

      {/* Archive (trash view) — swaps to delete button when words are selected */}
      <AnimatePresence mode="wait">
        {selectedCount > 0 ? (
          <motion.button
            key="delete"
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.7 }}
            transition={{ duration: 0.15 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onDelete}
            title={`Delete ${selectedCount} selected`}
            className="relative w-8 h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-red-400 hover:bg-red-50 hover:border-red-200 hover:text-red-500 transition-all overflow-visible flex-shrink-0"
          >
            <Trash2 size={14} />
            <motion.span
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
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
            transition={{ duration: 0.15 }}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={onOpenTrash}
            title="View trash"
            className="w-8 h-8 rounded-lg flex items-center justify-center border border-slate-200 bg-white text-slate-400 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-500 transition-all"
          >
            <ArchiveX size={14} />
          </motion.button>
        )}
      </AnimatePresence>
    </div>
  );
}

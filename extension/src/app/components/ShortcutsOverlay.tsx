import { motion } from "framer-motion";
import { X } from "lucide-react";
import { RADIUS, MOTION } from "../theme";

const SHORTCUTS: { key: string; label: string }[] = [
  { key: "/", label: "Focus search" },
  { key: "L", label: "List view" },
  { key: "R", label: "Review view" },
  { key: "S", label: "Stats view" },
  { key: "T", label: "Open trash" },
  { key: "E", label: "Export to Anki" },
  { key: "?", label: "Show this help" },
  { key: "Esc", label: "Close overlay" },
];

export function ShortcutsOverlay({ onClose }: { onClose: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={MOTION.fast}
      className="absolute inset-0 z-40 flex items-center justify-center px-6"
      style={{ background: "rgba(15,23,42,0.5)", backdropFilter: "blur(6px)" }}
      role="dialog"
      aria-modal="true"
      aria-label="Keyboard shortcuts"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 8 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0 }}
        transition={MOTION.spring}
        onClick={(e) => e.stopPropagation()}
        className="relative bg-white w-full overflow-hidden"
        style={{ borderRadius: RADIUS.lg, boxShadow: "0 24px 64px rgba(15,23,42,0.3)" }}
      >
        <div className="flex items-center justify-between px-4 pt-3 pb-2 border-b border-slate-100">
          <h3 className="text-[13px] font-bold text-slate-800">Keyboard shortcuts</h3>
          <button
            onClick={onClose}
            aria-label="Close"
            className="w-6 h-6 rounded-md flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X size={13} />
          </button>
        </div>
        <ul className="px-4 py-3 space-y-1.5">
          {SHORTCUTS.map((s) => (
            <li key={s.key} className="flex items-center justify-between">
              <span className="text-[12px] text-slate-600">{s.label}</span>
              <kbd
                className="px-1.5 py-0.5 text-[10.5px] font-mono font-bold text-slate-700 bg-slate-100 border border-slate-200 rounded"
                style={{ minWidth: 22, textAlign: "center" }}
              >
                {s.key}
              </kbd>
            </li>
          ))}
        </ul>
      </motion.div>
    </motion.div>
  );
}

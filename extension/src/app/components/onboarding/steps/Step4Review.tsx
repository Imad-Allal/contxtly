import { motion } from "framer-motion";
import { List, Repeat, BarChart3, Layers } from "lucide-react";
import { COLORS } from "../../../theme";
import { useReducedMotion } from "../../../hooks/useReducedMotion";

const FEATURES = [
  { icon: List, title: "Your list", body: "Browse, filter, and search every word you save.", color: COLORS.primary },
  { icon: Repeat, title: "Review mode", body: "Daily spaced-repetition so nothing slips away.", color: COLORS.noun },
  { icon: BarChart3, title: "Stats", body: "Track streaks and see progress by word type.", color: COLORS.compound },
  { icon: Layers, title: "Export", body: "Send to Anki, CSV, JSON, or Quizlet anytime.", color: COLORS.adjective },
];

export function Step4Review() {
  const reduced = useReducedMotion();

  return (
    <>
      <div className="grid grid-cols-2 gap-2 w-full max-w-[280px] mb-5">
        {FEATURES.map((f, i) => {
          const Icon = f.icon;
          return (
            <motion.div
              key={f.title}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduced ? 0 : i * 0.07, duration: 0.3 }}
              className="p-2.5 text-left"
              style={{
                borderRadius: 12,
                background: f.color.bg,
                border: `1px solid ${f.color.ring}`,
              }}
            >
              <div
                className="w-7 h-7 rounded-lg flex items-center justify-center mb-1.5"
                style={{ background: "white", color: f.color.accent }}
              >
                <Icon size={14} strokeWidth={2.2} />
              </div>
              <p className="text-[11px] font-bold mb-0.5" style={{ color: f.color.text }}>
                {f.title}
              </p>
              <p className="text-[10px] leading-snug" style={{ color: f.color.text, opacity: 0.75 }}>
                {f.body}
              </p>
            </motion.div>
          );
        })}
      </div>

      <h2 className="text-[18px] font-extrabold text-slate-800 mb-1">
        You're all set
      </h2>
      <p className="text-[12.5px] text-slate-500 leading-relaxed max-w-[280px]">
        Press <kbd className="px-1 py-0.5 text-[10px] font-mono bg-slate-100 rounded border border-slate-200">?</kbd> anytime to see keyboard shortcuts.
      </p>
    </>
  );
}

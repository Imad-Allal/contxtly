import { motion } from "framer-motion";
import { Search, BookOpen } from "lucide-react";
import { COLORS, MOTION } from "../theme";
import { useReducedMotion } from "../hooks/useReducedMotion";

export function EmptyState({ isSearch }: { isSearch: boolean }) {
  const reduced = useReducedMotion();
  const Icon = isSearch ? Search : BookOpen;
  const swatch = isSearch ? COLORS.slate : COLORS.primary;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.94 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={MOTION.base}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      <div className="relative">
        <motion.div
          animate={reduced ? undefined : { y: [0, -6, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          className="w-20 h-20 rounded-3xl flex items-center justify-center mb-4"
          style={{
            background: `linear-gradient(135deg, ${swatch.bg}, #ffffff)`,
            border: `1px solid ${swatch.ring}`,
            boxShadow: `0 8px 24px ${swatch.accent}22`,
          }}
        >
          <Icon size={30} style={{ color: swatch.accent }} strokeWidth={1.8} />
        </motion.div>
      </div>

      <h3 className="text-[14px] font-bold text-slate-700 mb-1.5">
        {isSearch ? "No matches found" : "Your collection is empty"}
      </h3>
      <p className="text-[11.5px] text-slate-500 max-w-[200px] leading-relaxed">
        {isSearch
          ? "Try a different search term or filter."
          : "Highlight any word on any webpage to start building your vocabulary."}
      </p>
    </motion.div>
  );
}

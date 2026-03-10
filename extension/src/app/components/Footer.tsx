import { motion, AnimatePresence } from "framer-motion";

interface FooterProps {
  wordCount: number;
  ankiStatus: { msg: string; error: boolean } | null;
}

export function Footer({ wordCount, ankiStatus }: FooterProps) {
  return (
    <footer
      className="flex items-center justify-between px-4 py-2.5 border-t border-white/60"
      style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.4)" }}
    >
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full bg-slate-300" />
        <span className="text-[11px] text-slate-500 font-semibold">
          {wordCount} word{wordCount !== 1 ? "s" : ""}
        </span>
      </div>

      <AnimatePresence mode="wait">
        {ankiStatus && (
          <motion.span
            key={ankiStatus.msg}
            initial={{ opacity: 0, y: 5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            transition={{ duration: 0.2 }}
            className="text-[11px] font-semibold"
            style={{ color: ankiStatus.error ? "#ef4444" : "#059669" }}
          >
            {ankiStatus.msg}
          </motion.span>
        )}
      </AnimatePresence>
    </footer>
  );
}

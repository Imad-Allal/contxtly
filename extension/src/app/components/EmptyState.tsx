import { motion } from "framer-motion";
import { Search, BookOpen, Sparkles } from "lucide-react";

export function EmptyState({ isSearch }: { isSearch: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.88 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="flex flex-col items-center justify-center py-12 px-4 text-center"
    >
      <motion.div
        animate={{ y: [0, -9, 0] }}
        transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
        className="relative w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-100/80 to-purple-100/80 flex items-center justify-center mb-4 shadow-sm"
        style={{ backdropFilter: "blur(8px)" }}
      >
        {isSearch ? (
          <Search className="text-blue-400" size={26} />
        ) : (
          <BookOpen className="text-purple-400" size={26} />
        )}
        <motion.div
          animate={{ scale: [1, 1.15, 1], opacity: [0.3, 0.6, 0.3] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-gradient-to-br from-blue-200 to-purple-200 flex items-center justify-center"
        >
          <Sparkles size={10} className="text-purple-500" />
        </motion.div>
      </motion.div>

      <h3 className="text-[13px] font-bold text-slate-700 mb-1.5">
        {isSearch ? "No matches found" : "No translations yet"}
      </h3>
      <p className="text-[11px] text-slate-400 max-w-[170px] leading-relaxed">
        {isSearch
          ? "Try a different search term"
          : "Highlight text on any webpage to start building your collection"}
      </p>

      {!isSearch && (
        <div className="flex gap-2 mt-5">
          {[0, 0.22, 0.44].map((delay, i) => (
            <motion.div
              key={i}
              animate={{ scale: [1, 1.5, 1], opacity: [0.35, 1, 0.35] }}
              transition={{ duration: 1.3, repeat: Infinity, delay, ease: "easeInOut" }}
              className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-blue-400 to-purple-500"
            />
          ))}
        </div>
      )}
    </motion.div>
  );
}

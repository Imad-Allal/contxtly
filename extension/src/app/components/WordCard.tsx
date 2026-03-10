import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ExternalLink } from "lucide-react";
import type { Word, TranslationData, TranslationDetail } from "../types";

const BAR_COLORS: Record<string, string> = {
  blue: "bg-blue-400",
  purple: "bg-violet-400",
  violet: "bg-violet-400",
  emerald: "bg-emerald-400",
  amber: "bg-[#bb0051]",
  rose: "bg-rose-400",
  slate: "bg-slate-400",
};

const TEXT_COLORS: Record<string, string> = {
  blue: "text-blue-600",
  purple: "text-violet-600",
  violet: "text-violet-600",
  emerald: "text-emerald-600",
  amber: "text-[#bb0051]",
  rose: "text-rose-600",
  slate: "text-slate-500",
};

const DETAIL_BG = "bg-slate-50/80 border-slate-100/80";

function getBreakdownColor(t: TranslationData): string {
  const wt = t.word_type;
  if (!wt) return t.collocation_pattern ? "amber" : "slate";
  const map: Record<string, string> = {
    conjugated_verb: "blue",
    separable_prefix: "blue",
    noun: "violet",
    plural_noun: "violet",
    collocation_verb: "amber",
    collocation_prep: "amber",
    fixed_expression: "rose",
    compound: "emerald",
  };
  return map[wt] || "slate";
}

function buildDisplayWord(word: Word, t: TranslationData | null): string {
  if (t?.collocation_pattern) {
    const parts = [word.text, ...(t.related_words || []).map((r) => r.text)];
    return `${parts.join("/")} (${t.collocation_pattern})`;
  }
  if (word.lemma && word.text !== word.lemma) {
    return `${word.text} (${word.lemma})`;
  }
  return word.text;
}

function buildDetails(word: Word): TranslationDetail[] {
  const t = typeof word.translation === "object" && word.translation !== null ? word.translation : null;
  const details: TranslationDetail[] = [];

  if (t) {
    const breakdownColor = getBreakdownColor(t);
    if (t.translation) details.push({ label: "Translation", color: "blue", text: t.translation });
    if (t.meaning) details.push({ label: "Meaning", color: "purple", text: t.meaning });
    if (t.breakdown) details.push({ label: "Breakdown", color: breakdownColor, text: t.breakdown });
    if (t.context_translation?.source) {
      details.push({
        label: "Context",
        color: "amber",
        source: t.context_translation.source,
        target: t.context_translation.target,
      });
    }
  } else if (typeof word.translation === "string") {
    details.push({ label: "Translation", color: "blue", text: word.translation });
  }

  return details;
}

function Checkbox({ checked, onToggle }: { checked: boolean; onToggle: () => void }) {
  return (
    <motion.div
      whileTap={{ scale: 0.8 }}
      className="flex-shrink-0"
      onClick={(e) => { e.stopPropagation(); onToggle(); }}
    >
      {checked ? (
        <motion.div
          initial={{ scale: 0.6 }}
          animate={{ scale: 1 }}
          className="w-[15px] h-[15px] rounded-[4px] bg-indigo-500 flex items-center justify-center shadow-sm shadow-indigo-100"
        >
          <svg className="w-[9px] h-[9px] text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </motion.div>
      ) : (
        <div className="w-[15px] h-[15px] rounded-[4px] border-[1.5px] border-slate-300 hover:border-blue-400 transition-colors" />
      )}
    </motion.div>
  );
}

function DetailItem({ detail, index }: { detail: TranslationDetail; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.045, duration: 0.22 }}
      className={`rounded-lg p-2 border text-[11px] ${DETAIL_BG}`}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <div className={`h-[3px] w-3 rounded-full ${BAR_COLORS[detail.color]}`} />
        <span className={`font-bold text-[9.5px] uppercase tracking-widest ${TEXT_COLORS[detail.color]}`}>
          {detail.label}
        </span>
      </div>
      {detail.source !== undefined ? (
        <div className="text-slate-600 leading-relaxed space-y-0.5">
          <p className="italic">"{detail.source}"</p>
          <p className="text-slate-500">&rarr; "{detail.target}"</p>
        </div>
      ) : (
        <p className="text-slate-600 leading-relaxed">{detail.text}</p>
      )}
    </motion.div>
  );
}

interface WordCardProps {
  word: Word;
  index: number;
  isSelected: boolean;
  isExpanded: boolean;
  onToggleSelect: (key: string) => void;
  onToggleExpand: (key: string) => void;
  onOpenUrl: (url: string) => void;
}

export function WordCard({
  word, index, isSelected, isExpanded, onToggleSelect, onToggleExpand, onOpenUrl,
}: WordCardProps) {
  const key = word.lemma || word.text;
  const t = typeof word.translation === "object" && word.translation !== null ? word.translation : null;
  const previewText = t?.translation || (typeof word.translation === "string" ? word.translation : null);
  const displayWord = buildDisplayWord(word, t);
  const details = buildDetails(word);

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.055, duration: 0.38, ease: [0.25, 0.46, 0.45, 0.94] }}
      whileHover={{ scale: 1.012, transition: { duration: 0.18 } }}
      className={`relative rounded-xl border cursor-pointer overflow-hidden transition-all duration-200 ${
        isSelected
          ? "bg-white border-slate-300 shadow-sm ring-[1.5px] ring-slate-300/70"
          : "bg-white/55 border-white/70 shadow-sm hover:shadow-md hover:bg-white/80"
      }`}
      style={{ backdropFilter: "blur(8px)" }}
      onClick={() => onToggleExpand(key)}
    >
      <div className="px-3 py-2.5">
        <div className="flex items-center gap-2.5">
          <Checkbox checked={isSelected} onToggle={() => onToggleSelect(key)} />
          <span className="flex-1 font-semibold text-slate-800 text-[13px] leading-snug min-w-0 truncate">
            {displayWord}
          </span>
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={{ duration: 0.22, ease: "easeInOut" }}
            className="flex-shrink-0 text-slate-400"
          >
            <ChevronDown size={14} />
          </motion.div>
        </div>

        {!isExpanded && previewText && (
          <p className="mt-1 ml-[27px] text-[11px] text-slate-500 truncate leading-relaxed">
            {previewText}
          </p>
        )}

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.27, ease: [0.04, 0.62, 0.23, 0.98] }}
              style={{ overflow: "hidden" }}
            >
              <div className="mt-2.5 pt-2.5 border-t border-slate-100/80 space-y-1.5">
                {details.map((detail, i) => (
                  <DetailItem key={detail.label} detail={detail} index={i} />
                ))}
                {word.url && (
                  <motion.button
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: details.length * 0.045 + 0.05 }}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={(e) => { e.stopPropagation(); onOpenUrl(word.url!); }}
                    className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-semibold text-white bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-500 hover:to-slate-600 shadow-sm transition-all"
                  >
                    <ExternalLink size={11} />
                    View source
                  </motion.button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}

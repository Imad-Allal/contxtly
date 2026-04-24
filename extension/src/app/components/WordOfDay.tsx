import { useEffect, useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, X } from "lucide-react";
import type { Word, TranslationData } from "../types";
import { COLORS, ELEVATION, MOTION, RADIUS, colorsForType, type WordTypeColorKey } from "../theme";
import { useReducedMotion } from "./../hooks/useReducedMotion";

const DISMISS_KEY = "wotd_dismissed_date";

const WORD_TYPE_MAP: Record<string, WordTypeColorKey> = {
  conjugated_verb: "verb", separable_prefix: "verb", verb: "verb",
  noun: "noun", plural_noun: "noun",
  adjective: "adjective",
  collocation_verb: "collocation", collocation_prep: "collocation", collocation: "collocation",
  fixed_expression: "expression", expression: "expression",
  compound: "compound",
};

function todayStr(): string {
  const d = new Date();
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}

function hash(s: string): number {
  let h = 5381;
  for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0;
  return h;
}

function typeKeyOf(w: Word): WordTypeColorKey | null {
  const t = typeof w.translation === "object" ? (w.translation as TranslationData) : null;
  if (!t) return null;
  if (t.verb_variant === "modal") return "verb_modal";
  if (t.verb_variant === "compound") return "verb_compound";
  if (t.word_type && WORD_TYPE_MAP[t.word_type]) return WORD_TYPE_MAP[t.word_type];
  if (t.collocation_pattern) return "collocation";
  return null;
}

interface Props {
  words: Word[];
  onOpen: (word: Word) => void;
}

export function WordOfDay({ words, onOpen }: Props) {
  const reduced = useReducedMotion();
  const [dismissedDate, setDismissedDate] = useState<string | null>(null);

  useEffect(() => {
    chrome.storage.local.get(DISMISS_KEY).then((r) => setDismissedDate((r[DISMISS_KEY] as string | undefined) ?? null));
  }, []);

  const pick = useMemo<Word | null>(() => {
    if (words.length === 0) return null;
    const idx = hash(todayStr()) % words.length;
    return words[idx];
  }, [words]);

  if (!pick) return null;
  if (dismissedDate === todayStr()) return null;

  const typeKey = typeKeyOf(pick);
  const swatch = typeKey ? colorsForType(typeKey) : COLORS.primary;
  const t = typeof pick.translation === "object" ? (pick.translation as TranslationData) : null;
  const preview = t?.translation || (typeof pick.translation === "string" ? pick.translation : "");

  async function dismiss(e: React.MouseEvent) {
    e.stopPropagation();
    const today = todayStr();
    await chrome.storage.local.set({ [DISMISS_KEY]: today });
    setDismissedDate(today);
  }

  return (
    <AnimatePresence>
      <motion.button
        initial={{ opacity: 0, y: reduced ? 0 : -6 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.96 }}
        transition={MOTION.base}
        whileHover={reduced ? undefined : { scale: 1.01 }}
        onClick={() => onOpen(pick)}
        className="relative w-full text-left overflow-hidden"
        style={{
          borderRadius: RADIUS.lg,
          background: `linear-gradient(135deg, ${swatch.bg}, #ffffff)`,
          border: `1px solid ${swatch.ring}`,
          boxShadow: ELEVATION[2],
          padding: "10px 12px",
        }}
      >
        <div className="flex items-start gap-2.5">
          <div
            className="flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center"
            style={{ background: "white", border: `1px solid ${swatch.ring}`, color: swatch.accent }}
          >
            <Sparkles size={14} strokeWidth={2.2} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-1.5 mb-0.5">
              <span className="text-[9px] font-bold uppercase tracking-widest" style={{ color: swatch.accent }}>
                Word of the day
              </span>
            </div>
            <p className="text-[13px] font-bold truncate" style={{ color: swatch.text }}>
              {pick.text}
            </p>
            {preview && (
              <p className="text-[11px] truncate leading-snug" style={{ color: swatch.text, opacity: 0.75 }}>
                {preview}
              </p>
            )}
          </div>
          <button
            onClick={dismiss}
            aria-label="Dismiss for today"
            className="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-slate-400 hover:text-slate-700 hover:bg-white/60 transition-colors"
          >
            <X size={12} />
          </button>
        </div>
      </motion.button>
    </AnimatePresence>
  );
}

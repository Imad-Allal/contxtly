import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, ExternalLink, Volume2, Globe, Check } from "lucide-react";
import { useState, useRef, useCallback } from "react";
import type { Word, TranslationData, TranslationDetail } from "../types";
import { COLORS, ELEVATION, MOTION, RADIUS, colorsForType, type WordTypeColorKey } from "../theme";
import { useReducedMotion } from "../hooks/useReducedMotion";

const WORD_TYPE_MAP: Record<string, WordTypeColorKey> = {
  conjugated_verb: "verb",
  separable_prefix: "verb",
  verb: "verb",
  noun: "noun",
  plural_noun: "noun",
  adjective: "adjective",
  collocation_verb: "collocation",
  collocation_prep: "collocation",
  collocation: "collocation",
  fixed_expression: "expression",
  expression: "expression",
  compound: "compound",
};

function wordTypeKey(t: TranslationData | null): WordTypeColorKey | null {
  if (!t) return null;
  if (t.verb_variant === "modal") return "verb_modal";
  if (t.verb_variant === "compound") return "verb_compound";
  if (t.word_type && WORD_TYPE_MAP[t.word_type]) return WORD_TYPE_MAP[t.word_type];
  if (t.collocation_pattern) return "collocation";
  return null;
}

function hostOf(url?: string): string | null {
  if (!url) return null;
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return null;
  }
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

function buildDetails(word: Word, typeKey: WordTypeColorKey | null): TranslationDetail[] {
  const t = typeof word.translation === "object" && word.translation !== null ? word.translation : null;
  const details: TranslationDetail[] = [];
  const breakdownColor = typeKey ?? "slate";

  if (t) {
    if (t.translation) details.push({ label: "Translation", color: "primary", text: t.translation });
    if (t.meaning) details.push({ label: "Meaning", color: "slate", text: t.meaning });
    if (t.breakdown) details.push({ label: "Breakdown", color: breakdownColor, text: t.breakdown });
    if (t.context_translation?.source) {
      details.push({
        label: "Context",
        color: "slate",
        source: t.context_translation.source,
        target: t.context_translation.target,
      });
    }
  } else if (typeof word.translation === "string") {
    details.push({ label: "Translation", color: "primary", text: word.translation });
  }

  return details;
}

function SelectionRail({
  selected,
  onToggle,
  accent,
}: {
  selected: boolean;
  onToggle: () => void;
  accent: string;
}) {
  return (
    <div
      data-selected={selected ? "true" : "false"}
      className="selection-rail absolute left-0 top-0 bottom-0 z-10 cursor-pointer"
      style={{ width: 28, ["--rail-accent" as string]: accent }}
      onClick={(e) => { e.stopPropagation(); onToggle(); }}
      role="checkbox"
      aria-checked={selected}
      aria-label={selected ? "Deselect word" : "Select word"}
    >
      <div className="selection-rail__stripe" />
      <div className="selection-rail__panel">
        <Check className="selection-rail__check" strokeWidth={4} aria-hidden="true" />
      </div>
    </div>
  );
}

function DetailItem({ detail, index }: { detail: TranslationDetail; index: number }) {
  const swatch = COLORS[detail.color as keyof typeof COLORS] ?? COLORS.slate;
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.04, ...MOTION.base }}
      className="rounded-lg p-2 border text-[11px]"
      style={{ background: swatch.bg, borderColor: swatch.ring }}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <div className="h-[3px] w-3 rounded-full" style={{ background: swatch.accent }} />
        <span className="font-bold text-[9.5px] uppercase tracking-widest" style={{ color: swatch.text }}>
          {detail.label}
        </span>
      </div>
      {detail.source !== undefined ? (
        <div className="text-slate-600 leading-relaxed space-y-0.5">
          <p className="italic">"{detail.source}"</p>
          <p className="text-slate-500">→ "{detail.target}"</p>
        </div>
      ) : (
        <p className="leading-relaxed" style={{ color: swatch.text }}>{detail.text}</p>
      )}
    </motion.div>
  );
}

function PronounceButton({ text, lang }: { text: string; lang?: string }) {
  const [speaking, setSpeaking] = useState(false);

  function speak(e: React.MouseEvent) {
    e.stopPropagation();
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    if (lang) u.lang = lang;
    u.onend = () => setSpeaking(false);
    u.onerror = () => setSpeaking(false);
    setSpeaking(true);
    window.speechSynthesis.speak(u);
  }

  return (
    <motion.button
      whileHover={{ scale: 1.08 }}
      whileTap={{ scale: 0.92 }}
      onClick={speak}
      aria-label={`Pronounce ${text}`}
      className="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
    >
      <motion.div animate={speaking ? { scale: [1, 1.2, 1] } : {}} transition={{ duration: 0.6, repeat: speaking ? Infinity : 0 }}>
        <Volume2 size={12} />
      </motion.div>
    </motion.button>
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
  sourceLang?: string;
  autoExpandOnHover?: boolean;
}

export function WordCard({
  word, index, isSelected, isExpanded, onToggleSelect, onToggleExpand, onOpenUrl, sourceLang, autoExpandOnHover,
}: WordCardProps) {
  const reduced = useReducedMotion();
  const hoverTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleMouseEnter = useCallback(() => {
    if (!autoExpandOnHover || isExpanded) return;
    hoverTimer.current = setTimeout(() => {
      onToggleExpand(word.lemma || word.text);
    }, 400);
  }, [autoExpandOnHover, isExpanded, onToggleExpand, word.lemma, word.text]);

  const handleMouseLeave = useCallback(() => {
    if (!autoExpandOnHover) return;
    if (hoverTimer.current) {
      clearTimeout(hoverTimer.current);
      hoverTimer.current = null;
    }
    if (isExpanded) onToggleExpand(word.lemma || word.text);
  }, [autoExpandOnHover, isExpanded, onToggleExpand, word.lemma, word.text]);
  const key = word.lemma || word.text;
  const t = typeof word.translation === "object" && word.translation !== null ? word.translation : null;
  const previewText = t?.translation || (typeof word.translation === "string" ? word.translation : null);
  const displayWord = buildDisplayWord(word, t);
  const typeKey = wordTypeKey(t);
  const swatch = typeKey ? colorsForType(typeKey) : COLORS.slate;
  const details = buildDetails(word, typeKey);
  const sourceUrl = word.url || word.source_url;
  const sourceHost = hostOf(sourceUrl);

  const delay = reduced ? 0 : Math.min(index * 0.03, 0.3);

  return (
    <motion.div
      data-word-key={key}
      initial={{ opacity: 0, y: reduced ? 0 : 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay, ...MOTION.base }}
      className="relative cursor-pointer overflow-hidden transition-shadow"
      style={{
        borderRadius: RADIUS.lg,
        background: isSelected ? "#ffffff" : "rgba(255,255,255,0.7)",
        border: `1px solid ${isSelected ? swatch.ring : "rgba(255,255,255,0.8)"}`,
        boxShadow: isSelected ? ELEVATION[2] : ELEVATION[1],
      }}
      onClick={() => onToggleExpand(key)}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <SelectionRail
        selected={isSelected}
        onToggle={() => onToggleSelect(key)}
        accent={swatch.accent}
      />
      <div className="px-3 py-2.5 pl-[26px]">
        <div className="flex items-center gap-2.5">
          <span className="flex-1 font-semibold text-slate-800 text-[13px] leading-snug min-w-0 truncate">
            {displayWord}
          </span>
          <PronounceButton text={word.text} lang={sourceLang} />
          <motion.div
            animate={{ rotate: isExpanded ? 180 : 0 }}
            transition={MOTION.fast}
            className="flex-shrink-0 text-slate-400"
          >
            <ChevronDown size={14} />
          </motion.div>
        </div>

        {!isExpanded && (previewText || sourceHost) && (
          <div className="mt-1 flex items-center gap-1.5 min-w-0">
            {previewText && (
              <p className="text-[11px] text-slate-500 truncate leading-relaxed flex-1 min-w-0">
                {previewText}
              </p>
            )}
            {sourceHost && (
              <button
                onClick={(e) => { e.stopPropagation(); if (sourceUrl) onOpenUrl(sourceUrl); }}
                aria-label={`Open source: ${sourceHost}`}
                className="flex-shrink-0 inline-flex items-center gap-1 px-1.5 py-[1px] text-[10px] font-medium text-slate-500 hover:text-rose-600 hover:bg-rose-50 rounded-md transition-colors max-w-[110px]"
              >
                <Globe size={9} />
                <span className="truncate">{sourceHost}</span>
              </button>
            )}
          </div>
        )}

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={MOTION.base}
              style={{ overflow: "hidden" }}
            >
              <div className="mt-2.5 pt-2.5 border-t border-slate-100 space-y-1.5">
                {details.map((detail, i) => (
                  <DetailItem key={detail.label} detail={detail} index={i} />
                ))}
                {word.url && (
                  <motion.button
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: details.length * 0.04 + 0.05 }}
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

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Eye, Sparkles, Volume2 } from "lucide-react";
import type { Word, TranslationData } from "../types";
import { useReview, type Grade } from "../hooks/useReview";
import { COLORS, ELEVATION, MOTION, RADIUS, colorsForType, type WordTypeColorKey } from "../theme";
import { useReducedMotion } from "../hooks/useReducedMotion";

const WORD_TYPE_MAP: Record<string, WordTypeColorKey> = {
  conjugated_verb: "verb", separable_prefix: "verb", verb: "verb",
  noun: "noun", plural_noun: "noun",
  adjective: "adjective",
  collocation_verb: "collocation", collocation_prep: "collocation", collocation: "collocation",
  fixed_expression: "expression", expression: "expression",
  compound: "compound",
};

function typeKeyOf(w: Word): WordTypeColorKey | null {
  const t = typeof w.translation === "object" ? (w.translation as TranslationData) : null;
  if (!t) return null;
  if (t.verb_variant === "modal") return "verb_modal";
  if (t.verb_variant === "compound") return "verb_compound";
  if (t.word_type && WORD_TYPE_MAP[t.word_type]) return WORD_TYPE_MAP[t.word_type];
  if (t.collocation_pattern) return "collocation";
  return null;
}

function displayForm(w: Word, t: TranslationData | null): string {
  if (!t) return w.lemma || w.text;
  if (t.collocation_pattern) {
    const m = t.collocation_pattern.match(/^(\S+)\s*\+\s*(\S+)$/);
    if (m) {
      const [, verb, prep] = m;
      return `${prep} etwas ${verb}`;
    }
    return t.collocation_pattern;
  }
  return w.lemma || w.text;
}

const STOPPER = /[,.;:!?—–]|\s-\s/g;

const TYPE_LABELS: Record<string, string> = {
  verb: "Verb",
  verb_modal: "Modal",
  verb_compound: "Perfekt",
  noun: "Noun",
  adjective: "Adjective",
  collocation: "Collocation",
  expression: "Expression",
  compound: "Compound",
};
const MIN_WORDS = 5;

function trimToSentence(raw: string | undefined, word: string): string {
  if (!raw) return "";
  const text = raw.trim();
  if (!word) return text;

  const stops: number[] = [-1];
  for (const m of text.matchAll(STOPPER)) {
    if (m.index === undefined) continue;
    if (m[0] === "." && m.index > 0 && /\d/.test(text[m.index - 1])) continue;
    stops.push(m.index);
  }
  stops.push(text.length);

  const wIdx = text.toLowerCase().indexOf(word.toLowerCase());
  if (wIdx < 0) return text;
  const wEnd = wIdx + word.length;

  let L = 0;
  for (let i = 0; i < stops.length; i++) {
    if (stops[i] < wIdx) L = i;
  }
  let R = stops.length - 1;
  for (let i = 0; i < stops.length; i++) {
    if (stops[i] >= wEnd) { R = i; break; }
  }

  const slice = (l: number, r: number) => text.slice(stops[l] + 1, stops[r]).trim();
  const count = (s: string) => (s ? s.split(/\s+/).filter(Boolean).length : 0);

  let result = slice(L, R);
  while (count(result) < MIN_WORDS && (L > 0 || R < stops.length - 1)) {
    if (R < stops.length - 1) R++;
    else L--;
    result = slice(L, R);
  }
  return result;
}

function highlightWord(sentence: string, word: string) {
  if (!word) return sentence;
  const idx = sentence.toLowerCase().indexOf(word.toLowerCase());
  if (idx < 0) return sentence;
  const before = sentence.slice(0, idx);
  const match = sentence.slice(idx, idx + word.length);
  const after = sentence.slice(idx + word.length);
  return (
    <>
      {before}
      <span className="font-bold text-slate-700">{match}</span>
      {after}
    </>
  );
}

const GRADES: { value: Grade; label: string; hint: string; color: string; text: string }[] = [
  { value: "again", label: "Again", hint: "<1m",   color: "#fef2f2", text: "#b91c1c" },
  { value: "hard",  label: "Hard",  hint: "1d",    color: "#fffbeb", text: "#92400e" },
  { value: "good",  label: "Good",  hint: "3d",    color: "#eef2ff", text: "#4338ca" },
  { value: "easy",  label: "Easy",  hint: "6d",    color: "#ecfdf5", text: "#065f46" },
];

export function ReviewView({ words, sourceLang }: { words: Word[]; sourceLang?: string }) {
  const { due, grade, loaded } = useReview(words);
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);
  const reduced = useReducedMotion();

  useEffect(() => {
    setIndex(0);
    setRevealed(false);
  }, [due.length]);

  if (!loaded) return <div className="flex-1" />;
  if (due.length === 0) return <ReviewEmpty />;

  const word = due[Math.min(index, due.length - 1)];
  if (!word) return <ReviewEmpty />;

  const typeKey = typeKeyOf(word);
  const swatch = typeKey ? colorsForType(typeKey) : COLORS.primary;
  const t = typeof word.translation === "object" ? (word.translation as TranslationData) : null;
  const translation = t?.translation || (typeof word.translation === "string" ? word.translation : "");
  const meaning = t?.meaning;
  const display = displayForm(word, t);
  const context = trimToSentence(word.context || t?.context_translation?.source, word.text);

  async function onGrade(g: Grade) {
    await grade(word, g);
    setRevealed(false);
    setIndex((i) => i + 1);
  }

  function pronounce() {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(word.text);
    if (sourceLang) u.lang = sourceLang;
    window.speechSynthesis.speak(u);
  }

  return (
    <div className="flex-1 flex flex-col px-3 py-3">
      <div className="flex items-center justify-between mb-2 px-1">
        <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
          {Math.min(index + 1, due.length)} of {due.length} due
        </span>
        <div className="flex-1 h-1 mx-3 rounded-full bg-slate-100 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{ background: COLORS.primary.accent }}
            animate={{ width: `${(Math.min(index, due.length) / due.length) * 100}%` }}
            transition={MOTION.base}
          />
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={word.localId + String(revealed)}
          initial={{ opacity: 0, y: reduced ? 0 : 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: reduced ? 0 : -12 }}
          transition={MOTION.base}
          className="flex-1 flex flex-col p-4 mb-3"
          style={{
            borderRadius: RADIUS.xl,
            background: `linear-gradient(160deg, ${swatch.bg}, #ffffff)`,
            border: `1px solid ${swatch.ring}`,
            boxShadow: ELEVATION[2],
          }}
        >
          <div className="flex items-center justify-between mb-3">
            {typeKey && (
              <span
                className="inline-flex items-center gap-1 px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest rounded-full"
                style={{ background: swatch.bg, color: swatch.text, border: `1px solid ${swatch.ring}` }}
              >
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: swatch.accent }} />
                {TYPE_LABELS[typeKey] ?? typeKey}
              </span>
            )}
            <motion.button
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.92 }}
              onClick={pronounce}
              aria-label={`Pronounce ${word.text}`}
              className="w-7 h-7 rounded-md flex items-center justify-center text-slate-400 hover:text-rose-600 hover:bg-white transition-colors"
            >
              <Volume2 size={13} />
            </motion.button>
          </div>

          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <h2 className="text-[26px] font-extrabold mb-2" style={{ color: swatch.text }}>
              {display}
            </h2>
            {context && (
              <p className="text-[12px] italic text-slate-500 leading-relaxed max-w-[280px] mb-3">
                "{highlightWord(context, word.text)}"
              </p>
            )}

            <AnimatePresence mode="wait">
              {revealed ? (
                <motion.div
                  key="back"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -6 }}
                  transition={MOTION.base}
                  className="w-full"
                >
                  {translation && (
                    <p className="text-[16px] font-bold" style={{ color: swatch.text }}>
                      {translation}
                    </p>
                  )}
                  {meaning && (
                    <p className="text-[12px] text-slate-500 leading-relaxed mt-1.5 max-w-[280px] mx-auto">
                      {meaning}
                    </p>
                  )}
                </motion.div>
              ) : (
                <motion.button
                  key="reveal"
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.96 }}
                  onClick={() => setRevealed(true)}
                  className="flex items-center gap-1.5 px-3.5 py-2 text-[12px] font-bold text-white rounded-xl"
                  style={{ background: swatch.accent, boxShadow: `0 4px 12px ${swatch.accent}55` }}
                >
                  <Eye size={13} />
                  Show translation
                </motion.button>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </AnimatePresence>

      {revealed && (
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={MOTION.base}
          className="grid grid-cols-4 gap-1.5"
        >
          {GRADES.map((g) => (
            <motion.button
              key={g.value}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.94 }}
              onClick={() => onGrade(g.value)}
              aria-label={`${g.label} — review again in ${g.hint}`}
              className="flex flex-col items-center justify-center py-2 transition-all"
              style={{
                borderRadius: RADIUS.md,
                background: g.color,
                border: `1px solid ${g.text}22`,
              }}
            >
              <span className="text-[12px] font-bold" style={{ color: g.text }}>{g.label}</span>
              <span className="text-[9px] font-medium mt-0.5" style={{ color: g.text, opacity: 0.7 }}>
                {g.hint}
              </span>
            </motion.button>
          ))}
        </motion.div>
      )}
    </div>
  );
}

function ReviewEmpty() {
  const reduced = useReducedMotion();
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
      <motion.div
        animate={reduced ? undefined : { scale: [1, 1.06, 1] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        className="w-20 h-20 rounded-3xl flex items-center justify-center mb-4"
        style={{
          background: `linear-gradient(135deg, ${COLORS.compound.bg}, #ffffff)`,
          border: `1px solid ${COLORS.compound.ring}`,
        }}
      >
        <Sparkles size={28} style={{ color: COLORS.compound.accent }} strokeWidth={1.8} />
      </motion.div>
      <h3 className="text-[14px] font-bold text-slate-700 mb-1">All caught up</h3>
      <p className="text-[11.5px] text-slate-500 leading-relaxed max-w-[220px]">
        Nothing is due right now. Save more words or come back tomorrow.
      </p>
    </div>
  );
}

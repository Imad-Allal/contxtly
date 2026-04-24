import { motion } from "framer-motion";
import { LANGUAGES } from "../../../constants";
import { COLORS, ELEVATION, RADIUS } from "../../../theme";
import { useReducedMotion } from "../../../hooks/useReducedMotion";

interface PreviewEntry {
  source: string;
  sourceLang: string;
  translation: string;
}

const PREVIEW: Record<string, PreviewEntry> = {
  en: { source: "teilnehmen", sourceLang: "de", translation: "to take part in" },
  es: { source: "teilnehmen", sourceLang: "de", translation: "participar en" },
  fr: { source: "teilnehmen", sourceLang: "de", translation: "participer à" },
  de: { source: "curiosity",  sourceLang: "en", translation: "Neugier" },
  it: { source: "teilnehmen", sourceLang: "de", translation: "partecipare a" },
  pt: { source: "teilnehmen", sourceLang: "de", translation: "participar de" },
  zh: { source: "teilnehmen", sourceLang: "de", translation: "参加" },
  ja: { source: "teilnehmen", sourceLang: "de", translation: "参加する" },
  ko: { source: "teilnehmen", sourceLang: "de", translation: "참가하다" },
  ar: { source: "teilnehmen", sourceLang: "de", translation: "يشارك في" },
  ru: { source: "teilnehmen", sourceLang: "de", translation: "участвовать" },
};

interface Props {
  targetLang: string;
  onLangChange: (lang: string) => void;
}

export function Step4Review({ targetLang, onLangChange }: Props) {
  const reduced = useReducedMotion();
  const preview = PREVIEW[targetLang] ?? PREVIEW.en;

  return (
    <>
      <div className="grid grid-cols-3 gap-1.5 w-full max-w-[280px] mb-3">
        {LANGUAGES.map((l, i) => {
          const active = targetLang === l.code;
          return (
            <motion.button
              key={l.code}
              onClick={() => onLangChange(l.code)}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: reduced ? 0 : i * 0.02, duration: 0.2 }}
              whileTap={{ scale: 0.96 }}
              className="relative px-2 py-1.5 text-[11px] font-semibold rounded-lg border transition-colors"
              style={
                active
                  ? {
                      background: COLORS.primary.bg,
                      color: COLORS.primary.text,
                      borderColor: COLORS.primary.ring,
                    }
                  : {
                      background: "rgba(255,255,255,0.7)",
                      color: "#475569",
                      borderColor: "#e2e8f0",
                    }
              }
            >
              {l.label}
            </motion.button>
          );
        })}
      </div>

      <motion.div
        key={targetLang}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.22 }}
        className="relative w-full max-w-[280px] overflow-hidden text-left"
        style={{
          borderRadius: RADIUS.lg,
          background: "#ffffff",
          border: `1px solid ${COLORS.primary.ring}`,
          boxShadow: ELEVATION[2],
        }}
      >
        <div
          className="absolute left-0 top-0 bottom-0"
          style={{ width: 4, background: COLORS.primary.accent }}
        />
        <div className="px-3 py-2.5 pl-4">
          <div className="flex items-center gap-1.5 mb-1">
            <span
              className="inline-flex items-center gap-1 px-1.5 py-[1px] text-[8.5px] font-bold uppercase tracking-widest rounded"
              style={{
                background: COLORS.primary.bg,
                color: COLORS.primary.text,
                border: `1px solid ${COLORS.primary.ring}`,
              }}
            >
              Translation
            </span>
            <span className="text-[9px] text-slate-400 font-semibold uppercase">
              {preview.sourceLang}
            </span>
          </div>
          <p className="text-[13px] font-extrabold text-slate-800 leading-tight">
            {preview.source}
          </p>
          <p className="text-[11px] text-slate-500 leading-snug mt-0.5">
            → {preview.translation}
          </p>
        </div>
      </motion.div>

      <h2 className="text-[15px] font-extrabold text-slate-800 mt-4">
        Pick your language
      </h2>
      <p className="text-[11px] text-slate-500 leading-relaxed max-w-[280px]">
        Every translation is delivered in this language. You can change it anytime in settings.
      </p>
    </>
  );
}

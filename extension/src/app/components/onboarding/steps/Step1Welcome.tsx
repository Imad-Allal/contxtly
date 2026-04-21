import { motion } from "framer-motion";
import { BookOpen } from "lucide-react";
import { COLORS, ELEVATION, RADIUS } from "../../../theme";
import { useReducedMotion } from "../../../hooks/useReducedMotion";
import { ContxtlyLogo } from "../../../ContxtlyLogo";

const PREVIEW_WORDS = [
  { word: "teilnehmen", gloss: "to take part in", tint: COLORS.collocation, type: "Collocation" },
  { word: "découvrir",  gloss: "to discover",     tint: COLORS.verb,        type: "Verb" },
  { word: "palazzo",    gloss: "palace",          tint: COLORS.noun,        type: "Noun" },
];

export function Step1Welcome() {
  const reduced = useReducedMotion();

  return (
    <>
      {/* Hero */}
      <div className="relative mb-4 flex items-center justify-center" style={{ width: 180, height: 120 }}>
        <motion.div
          initial={{ scale: 0.5, rotate: -8 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 18 }}
          style={{ width: 72, height: 72 }}
        >
          <ContxtlyLogo size={72} reduced={reduced} />
        </motion.div>
      </div>

      {/* Welcome headline */}
      <h2 className="text-[22px] font-extrabold text-slate-800 mb-1 leading-tight tracking-tight">
        Welcome to Contxtly
      </h2>
      <p className="text-[12.5px] text-slate-500 leading-relaxed max-w-[280px] mb-4">
        A personal dictionary that builds itself as you read — from every article, post, and page you come across.
      </p>

      {/* Fanned preview cards — a peek at the real aesthetic */}
      <div className="relative w-full max-w-[260px]" style={{ height: 138 }}>
        {PREVIEW_WORDS.map((p, i) => {
          const offsetY = i * 26;
          const rotate = (i - 1) * 2.5;
          return (
            <motion.div
              key={p.word}
              initial={{ opacity: 0, y: -12, rotate: 0 }}
              animate={{ opacity: 1, y: offsetY, rotate }}
              transition={{
                delay: reduced ? 0 : 0.2 + i * 0.12,
                type: "spring",
                stiffness: 220,
                damping: 18,
              }}
              className="absolute left-0 right-0 px-3 py-2 bg-white overflow-hidden"
              style={{
                borderRadius: RADIUS.lg,
                border: `1px solid ${p.tint.ring}`,
                boxShadow: ELEVATION[2],
                zIndex: PREVIEW_WORDS.length - i,
              }}
            >
              <div
                className="absolute left-0 top-2 bottom-2 w-[3px] rounded-r-full"
                style={{ background: p.tint.accent }}
              />
              <div className="flex items-center gap-2 pl-1.5">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span
                      className="inline-flex items-center gap-1 px-1.5 py-[1px] text-[8.5px] font-bold uppercase tracking-widest rounded"
                      style={{ background: p.tint.bg, color: p.tint.text, border: `1px solid ${p.tint.ring}` }}
                    >
                      <span className="w-1 h-1 rounded-full" style={{ background: p.tint.accent }} />
                      {p.type}
                    </span>
                  </div>
                  <p className="text-[12px] font-bold text-slate-800 truncate leading-tight">
                    {p.word}
                  </p>
                  <p className="text-[10.5px] text-slate-500 truncate leading-snug">
                    {p.gloss}
                  </p>
                </div>
                <div
                  className="flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center"
                  style={{ background: p.tint.bg, color: p.tint.accent }}
                >
                  <BookOpen size={11} strokeWidth={2.2} />
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>
    </>
  );
}

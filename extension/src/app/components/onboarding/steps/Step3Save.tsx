import { motion } from "framer-motion";
import { ChevronDown, Volume2, Globe } from "lucide-react";
import { COLORS, ELEVATION, RADIUS, type ColorSwatch } from "../../../theme";
import { useReducedMotion } from "../../../hooks/useReducedMotion";

interface SavedWord {
  word: string;
  translation: string;
  source: string;
  tint: ColorSwatch;
}

const EXISTING: SavedWord[] = [
  { word: "découvrir", translation: "to discover", source: "lemonde.fr",  tint: COLORS.verb },
  { word: "palazzo",   translation: "palace",      source: "repubblica.it", tint: COLORS.noun },
  { word: "flüchtig",  translation: "fleeting",    source: "zeit.de",      tint: COLORS.adjective },
];

const NEW_WORD: SavedWord = {
  word: "teilnehmen",
  translation: "to take part in",
  source: "spiegel.de",
  tint: COLORS.collocation,
};

function CardRow({
  entry,
  isNew,
}: {
  entry: SavedWord;
  isNew?: boolean;
}) {
  const { tint } = entry;
  return (
    <div
      className="relative overflow-hidden"
      style={{
        borderRadius: RADIUS.lg,
        background: isNew ? "#ffffff" : "rgba(255,255,255,0.7)",
        border: `1px solid ${isNew ? tint.ring : "rgba(255,255,255,0.9)"}`,
        boxShadow: isNew ? ELEVATION[2] : ELEVATION[1],
      }}
    >
      {/* Left accent rail */}
      <div
        className="absolute left-0 top-0 bottom-0"
        style={{ width: 4, background: tint.accent, opacity: isNew ? 1 : 0.8 }}
      />

      <div className="px-2.5 py-2 pl-4 text-left">
        <div className="flex items-center gap-2">
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-slate-800 text-[12px] leading-snug truncate">
              {entry.word}
            </p>
            <p className="text-[10px] text-slate-500 truncate leading-relaxed mt-0.5">
              {entry.translation}
            </p>
          </div>
          <span className="flex-shrink-0 inline-flex items-center gap-1 px-1 py-[1px] text-[9px] font-medium text-slate-500 rounded max-w-[96px]">
            <Globe size={8} />
            <span className="truncate">{entry.source}</span>
          </span>
          <div className="flex-shrink-0 w-5 h-5 rounded-md flex items-center justify-center text-slate-400">
            <Volume2 size={10} />
          </div>
          <div className="flex-shrink-0 text-slate-400">
            <ChevronDown size={11} />
          </div>
        </div>
      </div>
    </div>
  );
}

export function Step3Save() {
  const reduced = useReducedMotion();

  return (
    <>
      {/* Mini popup frame, to evoke the real extension surface */}
      <div
        className="w-full max-w-[280px] p-2.5"
        style={{
          borderRadius: RADIUS.xl,
          background:
            "linear-gradient(135deg, #f8fafc 0%, rgba(219,234,254,0.35) 50%, rgba(237,233,254,0.35) 100%)",
          border: "1px solid #e2e8f0",
          boxShadow: ELEVATION[2],
        }}
      >
        <div className="flex items-center justify-between mb-3 px-0.5">
          <p className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500">
            Your dictionary
          </p>
          <span className="text-[9px] font-semibold text-slate-400">
            {EXISTING.length + 1} words
          </span>
        </div>

        <div className="space-y-1.5">
          {/* Newly-saved word — drops in first on top */}
          <motion.div
            initial={{ opacity: 0, y: -10, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              delay: reduced ? 0 : 0.1,
              type: "spring",
              stiffness: 260,
              damping: 22,
            }}
            style={{ borderRadius: RADIUS.lg }}
          >
            <CardRow entry={NEW_WORD} isNew />
          </motion.div>

          {EXISTING.map((entry, i) => (
            <motion.div
              key={entry.word}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: reduced ? 0 : 0.3 + i * 0.1,
                type: "spring",
                stiffness: 260,
                damping: 24,
              }}
            >
              <CardRow entry={entry} />
            </motion.div>
          ))}
        </div>
      </div>

      <h2 className="text-[15px] font-extrabold text-slate-800 mt-6">
        Keep track of your words
      </h2>
      <p className="text-[11px] text-slate-500 leading-relaxed max-w-[280px]">
        Every word you save lands here — browse, search, and pick up right where you left off.
      </p>
    </>
  );
}

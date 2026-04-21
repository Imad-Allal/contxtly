import { CSSProperties, ReactNode } from "react";
import { motion } from "framer-motion";
import { MousePointer2, ArrowDown, Trash2 } from "lucide-react";
import { COLORS } from "../../../theme";
import { useReducedMotion } from "../../../hooks/useReducedMotion";

const COLLOC_BG = "rgba(187, 0, 81, 0.1)";
const COLLOC_UNDERLINE = "rgba(187, 0, 81, 0.55)";
const CARD_STYLE: CSSProperties = {
  borderRadius: 12,
  border: "1px solid #e2e8f0",
  boxShadow: "0 4px 14px rgba(15,23,42,0.06)",
};

// ── Sequential timeline (ms) — total ~3.6s ──────────────────────────────────
// Each step plays once and stays at its end state.
const T = {
  card1:        0,    // Card 1 fades in (CSS .onb-reveal handles this)
  selectStart:  300,  // Highlight starts sweeping across "nahmen" (no extra delay)
  selectEnd:    700,  // Highlight fully covers the word
  cursorIn:     300,  // Cursor fades in already on the word
  cursorMove:   700,  // Cursor glides toward the Translate tooltip position
  translate:    1000, // "Translate" tooltip pops up (stays)
  arrow:        1200, // Down arrow fades in
  card2:        1400, // Card 2 fades in with highlights
  tooltip:      1600, // Collocation card fades in
} as const;

const SELECT_DURATION = (T.selectEnd - T.selectStart) / 1000;       // 0.4s

// Cursor positions (px, relative to Card 1's padding box).
// Tweak these two if the cursor still doesn't land on the word / tooltip.
const CURSOR_ON_WORD   = { x: 149,  y: 35 };  // sits over "nahmen"
const CURSOR_ON_BUTTON = { x: 180, y: 55 };  // sits on the Translate tooltip

function Reveal({
  delay,
  children,
  className,
  style,
}: {
  delay: number;
  children: ReactNode;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div
      className={`onb-reveal ${className ?? ""}`}
      style={{ ...style, animationDelay: `${delay}ms` }}
    >
      {children}
    </div>
  );
}

export function Step2Highlight() {
  const reduced = useReducedMotion();
  const c = COLORS.collocation;

  const Highlight = ({ children }: { children: ReactNode }) => (
    <span
      style={{
        background: COLLOC_BG,
        boxShadow: `inset 0 -2px 0 ${COLLOC_UNDERLINE}`,
        borderRadius: 3,
        padding: "0 2px 1px",
        color: "#0f172a",
      }}
    >
      {children}
    </span>
  );

  return (
    <>
      <div className="w-full max-w-[280px] space-y-2">
        {/* Part 1 — user selecting */}
        <Reveal
          delay={T.card1}
          className="relative p-2.5 bg-white text-left"
          style={CARD_STYLE}
        >
          <p className="text-[9px] font-bold uppercase tracking-widest text-slate-400 mb-1">
            1. You select
          </p>
          <p className="text-[12px] text-slate-700 leading-relaxed select-none">
            Viele Studenten{" "}
            <motion.span
              initial={{ backgroundSize: "0% 100%" }}
              animate={{ backgroundSize: "100% 100%" }}
              transition={{
                duration: SELECT_DURATION,
                delay: T.selectStart / 1000,
                ease: "easeOut",
              }}
              style={{
                backgroundImage:
                  "linear-gradient(rgba(59,130,246,0.35), rgba(59,130,246,0.35))",
                backgroundRepeat: "no-repeat",
                backgroundPosition: "left center",
              }}
              className="px-0.5 rounded-[2px]"
            >
              nahmen
            </motion.span>{" "}
            an dem Workshop teil.
          </p>

          {/* Cursor: fades in on the word, then glides to the Translate tooltip */}
          <motion.div
            initial={{
              x: CURSOR_ON_WORD.x,
              y: CURSOR_ON_WORD.y,
              opacity: 0,
            }}
            animate={{
              x: [CURSOR_ON_WORD.x, CURSOR_ON_WORD.x, CURSOR_ON_BUTTON.x],
              y: [CURSOR_ON_WORD.y, CURSOR_ON_WORD.y, CURSOR_ON_BUTTON.y],
              opacity: [0, 1, 1],
            }}
            transition={{
              duration: (T.translate - T.cursorIn) / 1000,
              delay: T.cursorIn / 1000,
              ease: "easeInOut",
              times: [
                0,
                (T.cursorMove - T.cursorIn) / (T.translate - T.cursorIn),
                1,
              ],
            }}
            className="absolute pointer-events-none text-slate-700"
            style={{ top: 0, left: 0, zIndex: 2 }}
          >
            <MousePointer2 size={14} fill="currentColor" strokeWidth={1} stroke="#fff" />
          </motion.div>

          {/* Translate tooltip */}
          <motion.div
            initial={{ opacity: 0, y: -4, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{
              duration: 0.2,
              delay: T.translate / 1000,
              ease: "easeOut",
            }}
            className="absolute"
            style={{
              top: 46,
              left: 150,
              background: "#1e293b",
              color: "#f1f5f9",
              padding: "4px 10px",
              borderRadius: 7,
              fontSize: 11,
              fontWeight: 500,
              letterSpacing: "0.01em",
              boxShadow: "0 1px 3px rgba(0,0,0,0.18), 0 1px 2px rgba(0,0,0,0.1)",
              whiteSpace: "nowrap",
            }}
          >
            Translate
          </motion.div>
        </Reveal>

        {/* Divider arrow */}
        <Reveal delay={T.arrow} className="flex items-center justify-center">
          <motion.div
            animate={reduced ? undefined : { y: [0, 3, 0] }}
            transition={{ duration: 1.4, repeat: Infinity, ease: "easeInOut" }}
            className="w-5 h-5 rounded-full flex items-center justify-center"
            style={{ background: c.bg, color: c.accent, border: `1px solid ${c.ring}` }}
            aria-hidden
          >
            <ArrowDown size={11} strokeWidth={2.5} />
          </motion.div>
        </Reveal>

        {/* Part 2 — Contxtly translates */}
        <Reveal delay={T.card2} className="p-2.5 bg-white text-left" style={CARD_STYLE}>
          <p
            className="text-[9px] font-bold uppercase tracking-widest mb-1"
            style={{ color: c.accent }}
          >
            2. Contxtly translates
          </p>
          <p className="text-[12px] text-slate-700 leading-relaxed">
            Viele Studenten <Highlight>nahmen</Highlight> <Highlight>an</Highlight> dem Workshop{" "}
            <Highlight>teil</Highlight>.
          </p>
        </Reveal>

        {/* Tooltip */}
        <Reveal
          delay={T.tooltip}
          className="text-left overflow-hidden"
          style={{
            borderRadius: 12,
            background: "#ffffff",
            border: "1px solid rgba(0,0,0,0.07)",
            boxShadow: "0 8px 24px rgba(0,0,0,0.09), 0 2px 6px rgba(0,0,0,0.05)",
          }}
        >
          <div className="px-3 pt-2.5 pb-2">
            <div className="flex items-start justify-between mb-1.5">
              <span
                className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[8.5px] font-bold uppercase tracking-widest rounded"
                style={{ background: c.bg, color: c.text, border: `1px solid ${c.ring}` }}
              >
                <span className="w-1 h-1 rounded-full" style={{ background: c.accent }} />
                Collocation
              </span>
              <Trash2 size={11} className="text-slate-300" />
            </div>
            <p className="text-[13px] font-extrabold text-slate-800 leading-tight mb-0.5">
              to take part in
            </p>
            <p className="text-[10.5px] text-slate-500 leading-snug mb-1.5">
              To participate in something.
            </p>
            <div
              className="px-1.5 py-1 text-[9.5px] font-mono leading-snug rounded"
              style={{ background: c.bg, color: c.text, border: `1px solid ${c.ring}` }}
            >
              an etwas teilnehmen → nehmen + an + teil
            </div>
          </div>
        </Reveal>
      </div>

      <h2 className="text-[15px] font-extrabold text-slate-800 mt-3 mb-0.5">
        Select, and we translate
      </h2>
      <p className="text-[11px] text-slate-500 leading-relaxed max-w-[280px]">
        Highlight any word — Contxtly captures the whole expression in context.
      </p>
    </>
  );
}

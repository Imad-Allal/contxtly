import { motion } from "framer-motion";
import { Flame, BookMarked } from "lucide-react";
import type { Word } from "../types";
import { useStats } from "../hooks/useStats";
import { COLORS, MOTION, RADIUS } from "../theme";
import { useReducedMotion } from "../hooks/useReducedMotion";

const TYPE_ROWS: { key: keyof ReturnType<typeof useStats>["byType"]; label: string; color: keyof typeof COLORS }[] = [
  { key: "verb", label: "Verbs", color: "verb" },
  { key: "noun", label: "Nouns", color: "noun" },
  { key: "adjective", label: "Adjectives", color: "adjective" },
  { key: "collocation", label: "Collocations", color: "collocation" },
  { key: "expression", label: "Expressions", color: "expression" },
  { key: "compound", label: "Compounds", color: "compound" },
];

export function StatsPanel({ words }: { words: Word[] }) {
  const stats = useStats(words);
  const reduced = useReducedMotion();
  const maxType = Math.max(1, ...TYPE_ROWS.map((r) => stats.byType[r.key]));
  const maxDay = Math.max(1, ...stats.last14.map((d) => d.count));

  return (
    <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 custom-scroll">
      <div className="grid grid-cols-2 gap-2">
        <StatCard
          icon={<BookMarked size={14} />}
          label="Total words"
          value={stats.total}
          color={COLORS.primary}
        />
        <StatCard
          icon={<Flame size={14} />}
          label="Day streak"
          value={stats.streak}
          color={COLORS.adjective}
          suffix={stats.streak === 1 ? "day" : "days"}
        />
      </div>

      <section
        className="p-3"
        style={{ borderRadius: RADIUS.lg, background: "rgba(255,255,255,0.75)", border: "1px solid rgba(226,232,240,0.8)" }}
        aria-label="Words by type"
      >
        <h3 className="text-[11px] font-bold text-slate-700 mb-2.5">Breakdown by type</h3>
        <div className="space-y-2">
          {TYPE_ROWS.map((row) => {
            const c = COLORS[row.color];
            const count = stats.byType[row.key];
            const pct = (count / maxType) * 100;
            return (
              <div key={row.key} className="flex items-center gap-2">
                <span className="text-[10.5px] font-semibold w-20" style={{ color: c.text }}>
                  {row.label}
                </span>
                <div className="flex-1 h-2.5 rounded-full overflow-hidden" style={{ background: c.bg, border: `1px solid ${c.ring}` }}>
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: reduced ? `${pct}%` : `${pct}%` }}
                    transition={reduced ? { duration: 0 } : MOTION.base}
                    className="h-full rounded-full"
                    style={{ background: c.accent }}
                  />
                </div>
                <span
                  className="text-[10.5px] font-bold tabular-nums"
                  style={{ color: c.text, minWidth: 22, textAlign: "right" }}
                >
                  {count}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      <section
        className="p-3"
        style={{ borderRadius: RADIUS.lg, background: "rgba(255,255,255,0.75)", border: "1px solid rgba(226,232,240,0.8)" }}
        aria-label="Saves in the last 14 days"
      >
        <div className="flex items-center justify-between mb-2.5">
          <h3 className="text-[11px] font-bold text-slate-700">Last 14 days</h3>
          <span className="text-[10px] text-slate-400 font-medium">
            {stats.last14.reduce((s, d) => s + d.count, 0)} saves
          </span>
        </div>
        <div className="flex items-end gap-[3px] h-20" role="img" aria-label={`Daily saves: ${stats.last14.map(d => `${d.label} ${d.count}`).join(", ")}`}>
          {stats.last14.map((d, i) => {
            const h = (d.count / maxDay) * 100;
            return (
              <motion.div
                key={d.day}
                initial={{ height: 0 }}
                animate={{ height: `${Math.max(h, 3)}%` }}
                transition={{ delay: reduced ? 0 : i * 0.02, ...MOTION.base }}
                className="flex-1 rounded-t"
                style={{
                  background: d.count > 0
                    ? `linear-gradient(to top, ${COLORS.primary.accent}, ${COLORS.primary.ring})`
                    : "#e2e8f0",
                  minHeight: 3,
                }}
                title={`${d.label}: ${d.count}`}
              />
            );
          })}
        </div>
        <div className="flex items-center gap-[3px] mt-1">
          {stats.last14.map((d, i) => (
            <div
              key={d.day}
              className="flex-1 text-center text-[9px] text-slate-400 font-medium tabular-nums"
            >
              {i % 2 === 0 ? d.label[0] : ""}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function StatCard({
  icon, label, value, color, suffix,
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: typeof COLORS[keyof typeof COLORS];
  suffix?: string;
}) {
  return (
    <div
      className="p-3"
      style={{
        borderRadius: RADIUS.lg,
        background: `linear-gradient(135deg, ${color.bg}, #ffffff)`,
        border: `1px solid ${color.ring}`,
      }}
    >
      <div className="flex items-center gap-1.5 mb-1.5" style={{ color: color.accent }}>
        {icon}
        <span className="text-[10px] font-bold uppercase tracking-widest" style={{ color: color.text }}>
          {label}
        </span>
      </div>
      <div className="flex items-baseline gap-1.5">
        <span className="text-[24px] font-extrabold tabular-nums" style={{ color: color.text }}>
          {value}
        </span>
        {suffix && (
          <span className="text-[11px] font-semibold" style={{ color: color.text, opacity: 0.6 }}>
            {suffix}
          </span>
        )}
      </div>
    </div>
  );
}

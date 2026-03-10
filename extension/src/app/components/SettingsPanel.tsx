import { motion, AnimatePresence } from "framer-motion";
import { LANGUAGES } from "../constants";

interface SettingsPanelProps {
  open: boolean;
  targetLang: string;
  mode: string;
  onLangChange: (lang: string) => void;
  onModeChange: (mode: string) => void;
}

function SectionLabel({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-1.5 mb-1.5">
      <div className="h-[3px] w-3.5 rounded-full bg-slate-400" />
      <label className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500">{text}</label>
    </div>
  );
}

export function SettingsPanel({ open, targetLang, mode, onLangChange, onModeChange }: SettingsPanelProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3, ease: [0.04, 0.62, 0.23, 0.98] }}
          style={{ overflow: "hidden" }}
        >
          <div
            className="px-4 py-3 border-b border-white/60 space-y-3"
            style={{ backdropFilter: "blur(12px)", background: "rgba(248,250,252,0.7)" }}
          >
            <div>
              <SectionLabel text="Translate to" />
              <select
                value={targetLang}
                onChange={(e) => onLangChange(e.target.value)}
                className="w-full px-3 py-2 text-[12px] rounded-xl border border-blue-100 text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-200 transition-all cursor-pointer font-medium"
                style={{ background: "rgba(239,246,255,0.7)" }}
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>{l.label}</option>
                ))}
              </select>
            </div>

            <div>
              <SectionLabel text="Translation mode" />
              <select
                value={mode}
                onChange={(e) => onModeChange(e.target.value)}
                className="w-full px-3 py-2 text-[12px] rounded-xl border border-purple-100 text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-200 transition-all cursor-pointer font-medium"
                style={{ background: "rgba(245,243,255,0.7)" }}
              >
                <option value="simple">Simple</option>
                <option value="smart">{"\u2728"} Smart (with context)</option>
              </select>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

import { motion, AnimatePresence } from "framer-motion";
import { Zap, Settings2 } from "lucide-react";
import { LANGUAGES } from "../constants";
import { getCheckoutUrl, getPortalUrl, openUrl } from "../chrome-api";
import type { AuthState } from "../hooks/useAuth";

interface SettingsPanelProps {
  open: boolean;
  targetLang: string;
  mode: string;
  onLangChange: (lang: string) => void;
  onModeChange: (mode: string) => void;
  auth: AuthState;
}

function SectionLabel({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-1.5 mb-1.5">
      <div className="h-[3px] w-3.5 rounded-full bg-slate-400" />
      <label className="text-[9.5px] font-bold uppercase tracking-widest text-slate-500">{text}</label>
    </div>
  );
}

export function SettingsPanel({ open, targetLang, mode, onLangChange, onModeChange, auth }: SettingsPanelProps) {
  const isPro = auth.usage?.plan === "pro";

  async function handleSubscribe() {
    const url = await getCheckoutUrl();
    if (url) openUrl(url);
  }

  async function handleManage() {
    const url = await getPortalUrl();
    if (url) openUrl(url);
  }

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

            {auth.loggedIn && (
              <div>
                <SectionLabel text="Subscription" />
                <div
                  className="flex items-center justify-between px-3 py-2.5 rounded-xl"
                  style={{ background: isPro ? "rgba(237,233,254,0.7)" : "rgba(248,250,252,0.7)", border: `1px solid ${isPro ? "#ddd6fe" : "#e2e8f0"}` }}
                >
                  <div className="flex items-center gap-2">
                    {isPro
                      ? <Zap size={13} className="text-violet-500" />
                      : <Settings2 size={13} className="text-slate-400" />
                    }
                    <span className="text-[12px] font-semibold" style={{ color: isPro ? "#5b21b6" : "#475569" }}>
                      {isPro ? "Pro plan" : "Free plan"}
                    </span>
                    {!isPro && (
                      <span className="text-[10px] text-slate-400">{auth.usage?.limit ?? 50} translations/day</span>
                    )}
                  </div>
                  {isPro ? (
                    <button
                      onClick={handleManage}
                      className="text-[11px] font-semibold text-violet-600 hover:text-violet-800 transition-colors"
                    >
                      Manage
                    </button>
                  ) : (
                    <motion.button
                      whileHover={{ scale: 1.04 }}
                      whileTap={{ scale: 0.96 }}
                      onClick={handleSubscribe}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-white"
                      style={{ background: "linear-gradient(135deg, #4f46e5, #6366f1)", boxShadow: "0 2px 8px rgba(99,102,241,0.3)" }}
                    >
                      <Zap size={10} />
                      Upgrade
                    </motion.button>
                  )}
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

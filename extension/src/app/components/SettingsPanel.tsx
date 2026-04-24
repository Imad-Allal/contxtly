import { motion, AnimatePresence } from "framer-motion";
import { Crown, Globe, SlidersHorizontal } from "lucide-react";
import type { ReactNode } from "react";
import { LANGUAGES } from "../constants";
import { getCheckoutUrl, getPortalUrl, openUrl } from "../chrome-api";
import type { AuthState } from "../hooks/useAuth";
import { PRIMARY_GRADIENT } from "../theme";

interface SettingsPanelProps {
  open: boolean;
  targetLang: string;
  mode: string;
  onLangChange: (lang: string) => void;
  onModeChange: (mode: string) => void;
  auth: AuthState;
}

function Row({
  icon,
  label,
  sublabel,
  children,
}: {
  icon: ReactNode;
  label: string;
  sublabel?: string;
  children: ReactNode;
}) {
  return (
    <div className="flex items-center justify-between gap-3 py-2.5">
      <div className="flex items-center gap-2 min-w-0">
        <div className="w-7 h-7 flex items-center justify-center rounded-lg bg-white border border-slate-200 text-slate-500 flex-shrink-0">
          {icon}
        </div>
        <div className="flex flex-col min-w-0">
          <span className="text-[12px] font-semibold text-slate-700 leading-tight">{label}</span>
          {sublabel && (
            <span className="text-[10px] text-slate-400 leading-tight mt-0.5 truncate">{sublabel}</span>
          )}
        </div>
      </div>
      <div className="flex-shrink-0">{children}</div>
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
            className="px-4 py-1 border-b border-white/60 divide-y divide-slate-100"
            style={{ backdropFilter: "blur(12px)", background: "rgba(248,250,252,0.7)" }}
          >
            <Row icon={<Globe size={13} />} label="Language">
              <select
                value={targetLang}
                onChange={(e) => onLangChange(e.target.value)}
                aria-label="Translate to"
                className="px-3 py-1.5 text-[12px] font-semibold rounded-lg bg-white border border-slate-200 text-slate-700 focus:outline-none focus:ring-2 focus:ring-rose-200 focus:border-rose-300 cursor-pointer transition-all"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code}>{l.label}</option>
                ))}
              </select>
            </Row>

            <Row icon={<SlidersHorizontal size={13} />} label="Mode" sublabel={mode === "smart" ? "Context-aware translation" : "Literal word-by-word"}>
              <div className="relative inline-flex rounded-lg p-[2px] bg-slate-100 border border-slate-200">
                {(["simple", "smart"] as const).map((m) => {
                  const active = mode === m;
                  return (
                    <button
                      key={m}
                      onClick={() => onModeChange(m)}
                      aria-pressed={active}
                      className="relative px-2.5 py-1 text-[11px] font-semibold rounded-md transition-colors capitalize z-[1]"
                      style={{ color: active ? "#9d0044" : "#64748b" }}
                    >
                      {active && (
                        <motion.span
                          layoutId="mode-pill"
                          transition={{ type: "spring", stiffness: 320, damping: 26 }}
                          className="absolute inset-0 rounded-md bg-white"
                          style={{ zIndex: -1, boxShadow: "0 1px 2px rgba(15,23,42,0.08)" }}
                        />
                      )}
                      {m}
                    </button>
                  );
                })}
              </div>
            </Row>

            {/* {auth.loggedIn && (
              <Row
                icon={<Crown size={13} className={isPro ? "text-rose-600" : ""} />}
                label={isPro ? "Pro plan" : "Free plan"}
                sublabel={!isPro ? `${auth.usage?.limit ?? 50} translations/day` : undefined}
              >
                {isPro ? (
                  <button
                    onClick={handleManage}
                    className="text-[11px] font-semibold text-rose-600 hover:text-rose-700 transition-colors"
                  >
                    Manage
                  </button>
                ) : (
                  <motion.button
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.96 }}
                    onClick={handleSubscribe}
                    className="px-3 py-1.5 rounded-lg text-[11px] font-bold text-white"
                    style={{ background: PRIMARY_GRADIENT, boxShadow: "0 2px 8px rgba(187,0,81,0.3)" }}
                  >
                    Upgrade
                  </motion.button>
                )}
              </Row>
            )} */}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

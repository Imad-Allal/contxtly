import { motion } from "framer-motion";
import { Settings, LogIn, LogOut, Zap, List, Repeat, BarChart3 } from "lucide-react";
import { openUrl, getCheckoutUrl } from "../chrome-api";
import type { AuthState } from "../hooks/useAuth";
import { RADIUS, MOTION } from "../theme";
import logoUrl from "../assets/contxtly.svg";

export type AppTab = "list" | "review" | "stats";

interface HeaderProps {
  settingsOpen: boolean;
  onToggleSettings: () => void;
  auth: AuthState;
  onLogin: () => void;
  onLogout: () => void;
  tab: AppTab;
  onTabChange: (t: AppTab) => void;
}

const TABS: { value: AppTab; label: string; icon: typeof List }[] = [
  { value: "list", label: "List", icon: List },
  { value: "review", label: "Review", icon: Repeat },
  { value: "stats", label: "Stats", icon: BarChart3 },
];

export function Header({ settingsOpen, onToggleSettings, auth, onLogin, onLogout, tab, onTabChange }: HeaderProps) {
  const { loggedIn, usage } = auth;
  const nearLimit = usage && usage.used >= usage.limit * 0.8;
  const atLimit = usage && usage.used >= usage.limit;

  async function handleUpgrade() {
    const url = await getCheckoutUrl();
    if (url) openUrl(url);
  }

  return (
    <header
      className="flex flex-col px-4 pt-3 pb-2 border-b border-white/60 gap-2"
      style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)" }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <motion.img
            src={logoUrl}
            alt="Contxtly"
            whileHover={{ scale: 1.08 }}
            className="w-9 h-9 flex-shrink-0"
            style={{ borderRadius: RADIUS.md }}
          />
          <div>
            <h1 className="text-[15px] font-extrabold leading-none text-slate-800">Contxtly</h1>
            <p className="text-[10px] text-slate-400 leading-none mt-0.5 font-medium">Learn while you read</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <motion.button
            whileHover={{ scale: 1.07 }}
            whileTap={{ scale: 0.93 }}
            onClick={loggedIn ? onLogout : onLogin}
            aria-label={loggedIn ? "Log out" : "Log in with Google"}
            className="w-8 h-8 flex items-center justify-center transition-all"
            style={{
              borderRadius: RADIUS.md,
              background: "rgba(255,255,255,0.75)",
              color: "#64748b",
              border: "1px solid rgba(255,255,255,0.9)",
            }}
            title={loggedIn ? "Log out" : "Log in with Google"}
          >
            {loggedIn ? <LogOut size={15} /> : <LogIn size={15} />}
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.07 }}
            whileTap={{ scale: 0.93 }}
            onClick={onToggleSettings}
            aria-label="Settings"
            aria-pressed={settingsOpen}
            className="w-8 h-8 flex items-center justify-center transition-all"
            style={{
              borderRadius: RADIUS.md,
              ...(settingsOpen
                ? { background: "#4f46e5", color: "white", boxShadow: "0 2px 8px rgba(79,70,229,0.25)" }
                : { background: "rgba(255,255,255,0.75)", color: "#64748b", border: "1px solid rgba(255,255,255,0.9)" }),
            }}
          >
            <motion.div animate={{ rotate: settingsOpen ? 90 : 0 }} transition={MOTION.base}>
              <Settings size={16} />
            </motion.div>
          </motion.button>
        </div>
      </div>

      {loggedIn && (
        <>
          {/* Tab switcher */}
          <div
            className="relative flex items-center p-0.5 gap-0.5"
            style={{
              borderRadius: RADIUS.pill,
              background: "rgba(241,245,249,0.9)",
              border: "1px solid rgba(226,232,240,0.8)",
            }}
            role="tablist"
          >
            {TABS.map((t) => {
              const active = tab === t.value;
              const Icon = t.icon;
              return (
                <button
                  key={t.value}
                  role="tab"
                  aria-selected={active}
                  onClick={() => onTabChange(t.value)}
                  className="relative flex-1 flex items-center justify-center gap-1 py-1 text-[11px] font-semibold transition-colors"
                  style={{
                    borderRadius: RADIUS.pill,
                    color: active ? "#1e293b" : "#64748b",
                    zIndex: 1,
                  }}
                >
                  {active && (
                    <motion.div
                      layoutId="tab-pill"
                      transition={MOTION.spring}
                      className="absolute inset-0"
                      style={{
                        borderRadius: RADIUS.pill,
                        background: "white",
                        boxShadow: "0 1px 3px rgba(15,23,42,0.08)",
                        zIndex: -1,
                      }}
                    />
                  )}
                  <Icon size={11} />
                  {t.label}
                </button>
              );
            })}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1">
              <div className="flex-1 h-1.5 rounded-full bg-slate-100 overflow-hidden">
                <motion.div
                  className="h-full rounded-full"
                  style={{ background: atLimit ? "#ef4444" : nearLimit ? "#f59e0b" : "#6366f1" }}
                  initial={{ width: 0 }}
                  animate={{ width: usage ? `${Math.min((usage.used / usage.limit) * 100, 100)}%` : "0%" }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                />
              </div>
              <span className="text-[10px] font-semibold text-slate-500 whitespace-nowrap">
                {usage ? `${usage.used} / ${usage.limit} today` : "— / — today"}
              </span>
            </div>

            {(nearLimit || atLimit) && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleUpgrade}
                className="ml-2 flex items-center gap-1 px-2 py-0.5 rounded-lg text-[10px] font-bold text-white"
                style={{ background: "linear-gradient(135deg, #f59e0b, #f97316)" }}
              >
                <Zap size={10} />
                Upgrade
              </motion.button>
            )}
          </div>
        </>
      )}
    </header>
  );
}

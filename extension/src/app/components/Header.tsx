import { motion } from "framer-motion";
import { Languages, Settings, LogIn, LogOut, Zap } from "lucide-react";
import { openUrl, getCheckoutUrl } from "../chrome-api";
import type { AuthState } from "../hooks/useAuth";

interface HeaderProps {
  settingsOpen: boolean;
  onToggleSettings: () => void;
  auth: AuthState;
  onLogin: () => void;
  onLogout: () => void;
}

export function Header({ settingsOpen, onToggleSettings, auth, onLogin, onLogout }: HeaderProps) {
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
          <div className="relative flex-shrink-0">
            <motion.div
              whileHover={{ scale: 1.08 }}
              className="w-9 h-9 rounded-xl flex items-center justify-center shadow-lg"
              style={{
                background: "linear-gradient(135deg, #4f46e5, #6366f1)",
                boxShadow: "0 4px 12px rgba(99,102,241,0.25)",
              }}
            >
              <Languages className="text-white" size={18} />
            </motion.div>
            <span className="absolute -top-0.5 -right-0.5 flex h-2.5 w-2.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-emerald-400 border-2 border-white" />
            </span>
          </div>
          <div>
            <h1 className="text-[15px] font-extrabold leading-none text-slate-800">Contxtly</h1>
            <p className="text-[10px] text-slate-400 leading-none mt-0.5 font-medium">Contextual translator</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <motion.button
            whileHover={{ scale: 1.07 }}
            whileTap={{ scale: 0.93 }}
            onClick={loggedIn ? onLogout : onLogin}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200"
            style={{ background: "rgba(255,255,255,0.75)", color: "#64748b", border: "1px solid rgba(255,255,255,0.9)" }}
            title={loggedIn ? "Log out" : "Log in with Google"}
          >
            {loggedIn ? <LogOut size={15} /> : <LogIn size={15} />}
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.07 }}
            whileTap={{ scale: 0.93 }}
            onClick={onToggleSettings}
            className="w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-200"
            style={
              settingsOpen
                ? { background: "#4f46e5", color: "white", boxShadow: "0 2px 8px rgba(79,70,229,0.2)" }
                : { background: "rgba(255,255,255,0.75)", color: "#64748b", border: "1px solid rgba(255,255,255,0.9)" }
            }
          >
            <motion.div animate={{ rotate: settingsOpen ? 90 : 0 }} transition={{ duration: 0.28, ease: "easeInOut" }}>
              <Settings size={16} />
            </motion.div>
          </motion.button>
        </div>
      </div>

      {loggedIn && (
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
      )}
    </header>
  );
}

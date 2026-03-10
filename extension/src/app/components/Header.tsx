import { motion } from "framer-motion";
import { Languages, Settings } from "lucide-react";

interface HeaderProps {
  settingsOpen: boolean;
  onToggleSettings: () => void;
}

export function Header({ settingsOpen, onToggleSettings }: HeaderProps) {
  return (
    <header
      className="flex items-center justify-between px-4 py-3 border-b border-white/60"
      style={{ backdropFilter: "blur(12px)", background: "rgba(255,255,255,0.45)" }}
    >
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
    </header>
  );
}

import { motion } from "framer-motion";
import { COLORS, ELEVATION, MOTION, RADIUS } from "../theme";

interface Props {
  onDismiss: () => void;
}

export function LanguageNotice({ onDismiss }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={MOTION.base}
      className="absolute inset-0 z-50 flex items-center justify-center px-5"
      role="dialog"
      aria-modal="true"
      style={{ background: "rgba(15,23,42,0.35)", backdropFilter: "blur(6px)", WebkitBackdropFilter: "blur(6px)" }}
    >
      <motion.div
        initial={{ opacity: 0, y: 8, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 8, scale: 0.96 }}
        transition={MOTION.base}
        className="w-full max-w-[320px]"
        style={{
          borderRadius: RADIUS.lg,
          background: "linear-gradient(135deg, #ffffff, #faf7ff)",
          border: `1px solid ${COLORS.primary.ring}`,
          boxShadow: ELEVATION[3],
          padding: 18,
        }}
      >
        <p className="text-[13px] font-extrabold text-slate-900 leading-snug mb-2">
          Heads up — language support
        </p>
        <p className="text-[12px] text-slate-600 leading-relaxed">
          Contxtly translates many languages, but grammar breakdowns (collocations,
          separable verbs, compounds) are currently only available for{" "}
          <span className="font-semibold text-slate-800">German</span>. More languages are coming soon.
        </p>
        <button
          onClick={onDismiss}
          className="mt-4 w-full py-2 rounded-xl text-[12px] font-bold text-white transition-transform hover:scale-[1.02] active:scale-95"
          style={{ background: "linear-gradient(135deg, #9d0044, #bb0051)" }}
        >
          Got it
        </button>
      </motion.div>
    </motion.div>
  );
}

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, ArrowLeft, ArrowRight } from "lucide-react";
import { Step1Welcome } from "./steps/Step1Welcome";
import { Step2Highlight } from "./steps/Step2Highlight";
import { Step4Review } from "./steps/Step4Review";
import { PRIMARY_GRADIENT, RADIUS, MOTION } from "../../theme";
import { useReducedMotion } from "../../hooks/useReducedMotion";

const STEPS = [Step1Welcome, Step2Highlight, Step4Review];

interface Props {
  onFinish: () => void;
}

export function OnboardingOverlay({ onFinish }: Props) {
  const [step, setStep] = useState(0);
  const [dir, setDir] = useState<1 | -1>(1);
  const reduced = useReducedMotion();
  const Current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onFinish();
      if (e.key === "ArrowRight") next();
      if (e.key === "ArrowLeft") prev();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  });

  function next() {
    if (isLast) return onFinish();
    setDir(1);
    setStep((s) => Math.min(s + 1, STEPS.length - 1));
  }

  function prev() {
    if (step === 0) return;
    setDir(-1);
    setStep((s) => Math.max(s - 1, 0));
  }

  const slideOffset = reduced ? 0 : 40;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={MOTION.base}
      className="absolute inset-0 z-50 flex items-center justify-center"
      style={{
        background: "rgba(15,23,42,0.45)",
        backdropFilter: "blur(6px)",
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Welcome tutorial"
    >
      <motion.div
        initial={{ scale: 0.92, opacity: 0, y: 10 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.92, opacity: 0 }}
        transition={MOTION.spring}
        className="relative flex flex-col bg-white overflow-hidden"
        style={{
          width: 340,
          height: 500,
          borderRadius: RADIUS.xl,
          boxShadow: "0 24px 64px rgba(15,23,42,0.25)",
        }}
      >
        <button
          onClick={onFinish}
          aria-label="Skip tutorial"
          className="absolute top-3 right-3 z-10 w-7 h-7 rounded-lg flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
        >
          <X size={14} />
        </button>

        <div className="flex-1 relative overflow-hidden">
          <AnimatePresence mode="wait" custom={dir}>
            <motion.div
              key={step}
              custom={dir}
              initial={{ x: dir * slideOffset, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -dir * slideOffset, opacity: 0 }}
              transition={MOTION.base}
              className="absolute inset-0 px-6 pt-10 pb-4 flex flex-col items-center text-center"
            >
              <Current />
            </motion.div>
          </AnimatePresence>
        </div>

        <div className="flex items-center justify-between px-5 pb-5 pt-2">
          <button
            onClick={prev}
            disabled={step === 0}
            aria-label="Previous step"
            className="flex items-center gap-1 text-[12px] font-semibold text-slate-500 hover:text-slate-700 disabled:opacity-0 disabled:pointer-events-none transition-colors"
          >
            <ArrowLeft size={12} />
            Back
          </button>

          <div className="flex items-center gap-1.5" role="progressbar" aria-valuenow={step + 1} aria-valuemin={1} aria-valuemax={STEPS.length}>
            {STEPS.map((_, i) => (
              <motion.div
                key={i}
                animate={{
                  width: i === step ? 18 : 6,
                  backgroundColor: i === step ? "#6366f1" : "#cbd5e1",
                }}
                transition={MOTION.base}
                className="h-1.5 rounded-full"
              />
            ))}
          </div>

          <motion.button
            whileHover={{ scale: 1.04 }}
            whileTap={{ scale: 0.96 }}
            onClick={next}
            className="flex items-center gap-1 px-4 py-1.5 rounded-xl text-[12px] font-bold text-white shadow-md"
            style={{ background: PRIMARY_GRADIENT, boxShadow: "0 4px 12px rgba(99,102,241,0.3)" }}
          >
            {isLast ? "Start learning" : "Next"}
            {!isLast && <ArrowRight size={12} />}
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}

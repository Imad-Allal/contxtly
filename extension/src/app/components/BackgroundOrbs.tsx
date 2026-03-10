import { motion } from "framer-motion";

const ORBS = [
  {
    className: "w-80 h-80 bg-blue-400/[0.07]",
    style: { top: "-80px", left: "-70px" },
    animate: { x: [0, 28, -18, 0], y: [0, -18, 26, 0], scale: [1, 1.08, 0.93, 1] },
    duration: 9,
    delay: 0,
  },
  {
    className: "w-72 h-72 bg-slate-400/[0.07]",
    style: { top: "35%", right: "-55px" },
    animate: { x: [0, -22, 14, 0], y: [0, 18, -14, 0], scale: [1, 0.92, 1.08, 1] },
    duration: 11,
    delay: 2.5,
  },
  {
    className: "w-64 h-64 bg-indigo-400/[0.06]",
    style: { bottom: "-50px", left: "25%" },
    animate: { x: [0, 16, -24, 0], y: [0, 24, -10, 0], scale: [1, 1.05, 0.96, 1] },
    duration: 13,
    delay: 5,
  },
];

export function BackgroundOrbs() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {ORBS.map((orb, i) => (
        <motion.div
          key={i}
          className={`absolute rounded-full blur-[64px] ${orb.className}`}
          animate={orb.animate}
          transition={{ duration: orb.duration, repeat: Infinity, ease: "easeInOut", delay: orb.delay }}
          style={orb.style}
        />
      ))}
    </div>
  );
}

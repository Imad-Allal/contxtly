import type { Transition } from "framer-motion";

export type WordTypeColorKey =
  | "verb"
  | "noun"
  | "adjective"
  | "collocation"
  | "expression"
  | "compound";

export interface ColorSwatch {
  bg: string;
  ring: string;
  text: string;
  accent: string;
}

export const COLORS: Record<WordTypeColorKey | "primary" | "slate", ColorSwatch> = {
  verb:        { bg: "#eff6ff", ring: "#bfdbfe", text: "#1d4ed8", accent: "#60a5fa" },
  noun:        { bg: "#f5f3ff", ring: "#ddd6fe", text: "#5b21b6", accent: "#a78bfa" },
  adjective:   { bg: "#fffbeb", ring: "#fde68a", text: "#92400e", accent: "#f59e0b" },
  collocation: { bg: "#fff0f6", ring: "#f9a8c9", text: "#bb0051", accent: "#bb0051" },
  expression:  { bg: "#fff1f2", ring: "#fecdd3", text: "#9d174d", accent: "#fb7185" },
  compound:    { bg: "#ecfdf5", ring: "#a7f3d0", text: "#065f46", accent: "#34d399" },
  primary:     { bg: "#eef2ff", ring: "#c7d2fe", text: "#4338ca", accent: "#6366f1" },
  slate:       { bg: "#f8fafc", ring: "#e2e8f0", text: "#475569", accent: "#94a3b8" },
};

export const RADIUS = {
  sm: 8,
  md: 12,
  lg: 16,
  xl: 20,
  pill: 9999,
} as const;

export const ELEVATION = {
  0: "none",
  1: "0 1px 2px rgba(15,23,42,0.06), 0 1px 3px rgba(15,23,42,0.04)",
  2: "0 4px 12px rgba(15,23,42,0.08), 0 2px 4px rgba(15,23,42,0.05)",
  3: "0 12px 32px rgba(15,23,42,0.12), 0 4px 10px rgba(15,23,42,0.06)",
} as const;

export const MOTION: Record<string, Transition> = {
  spring:      { type: "spring", stiffness: 320, damping: 26 },
  springSoft:  { type: "spring", stiffness: 220, damping: 24 },
  fast:        { duration: 0.18, ease: [0.32, 0.72, 0, 1] },
  base:        { duration: 0.26, ease: [0.32, 0.72, 0, 1] },
  slow:        { duration: 0.4, ease: [0.32, 0.72, 0, 1] },
};

export const STAGGER = {
  listItem: 0.03,
  maxDelay: 0.3,
};

const TYPE_ALIASES: Record<string, WordTypeColorKey> = {
  verb: "verb",
  noun: "noun",
  adjective: "adjective",
  adj: "adjective",
  collocation: "collocation",
  colloc: "collocation",
  expression: "expression",
  expr: "expression",
  idiom: "expression",
  compound: "compound",
};

export function colorsForType(type?: string | null): ColorSwatch {
  if (!type) return COLORS.slate;
  return COLORS[TYPE_ALIASES[type.toLowerCase()] ?? "slate" as WordTypeColorKey] ?? COLORS.slate;
}

export const PRIMARY_GRADIENT = "linear-gradient(135deg, #4f46e5, #6366f1)";
export const BG_GRADIENT =
  "linear-gradient(135deg, #f8fafc 0%, rgba(219,234,254,0.25) 50%, rgba(237,233,254,0.25) 100%)";
export const FONT_STACK =
  "'Plus Jakarta Sans', ui-sans-serif, -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif";

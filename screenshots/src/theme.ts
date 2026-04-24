export type WordTypeColorKey =
  | "verb" | "noun" | "adjective" | "collocation" | "expression" | "compound";

export interface ColorSwatch {
  bg: string; ring: string; text: string; accent: string;
}

export const COLORS: Record<WordTypeColorKey | "primary" | "slate", ColorSwatch> = {
  verb:        { bg: "#eff6ff", ring: "#bfdbfe", text: "#1d4ed8", accent: "#60a5fa" },
  noun:        { bg: "#f5f3ff", ring: "#ddd6fe", text: "#5b21b6", accent: "#a78bfa" },
  adjective:   { bg: "#fffbeb", ring: "#fde68a", text: "#92400e", accent: "#f59e0b" },
  collocation: { bg: "#fff0f6", ring: "#f9a8c9", text: "#bb0051", accent: "#bb0051" },
  expression:  { bg: "#fff1f2", ring: "#fecdd3", text: "#9d174d", accent: "#fb7185" },
  compound:    { bg: "#ecfdf5", ring: "#a7f3d0", text: "#065f46", accent: "#34d399" },
  primary:     { bg: "#f3eaff", ring: "#d9b8ff", text: "#5200c7", accent: "#6c00ff" },
  slate:       { bg: "#f8fafc", ring: "#e2e8f0", text: "#475569", accent: "#94a3b8" },
};

export const HIGHLIGHT: Record<WordTypeColorKey, { bg: string; shadow: string }> = {
  verb:        { bg: "rgba(219,234,254,0.75)", shadow: "inset 0 -2px 0 rgba(96,165,250,0.85)" },
  noun:        { bg: "rgba(237,233,254,0.75)", shadow: "inset 0 -2px 0 rgba(167,139,250,0.85)" },
  adjective:   { bg: "rgba(254,243,199,0.75)", shadow: "inset 0 -2px 0 rgba(245,158,11,0.85)" },
  collocation: { bg: "rgba(187,0,81,0.18)",    shadow: "inset 0 -2px 0 rgba(187,0,81,0.85)" },
  expression:  { bg: "rgba(255,228,230,0.75)", shadow: "inset 0 -2px 0 rgba(251,113,133,0.85)" },
  compound:    { bg: "rgba(209,250,229,0.75)", shadow: "inset 0 -2px 0 rgba(52,211,153,0.85)" },
};

export const RADIUS = { sm: 8, md: 12, lg: 16, xl: 20, pill: 9999 } as const;

export const ELEVATION = {
  1: "0 1px 2px rgba(15,23,42,0.06), 0 1px 3px rgba(15,23,42,0.04)",
  2: "0 4px 12px rgba(15,23,42,0.08), 0 2px 4px rgba(15,23,42,0.05)",
  3: "0 12px 40px rgba(15,23,42,0.14), 0 6px 16px rgba(15,23,42,0.08)",
  4: "0 30px 80px rgba(15,23,42,0.20), 0 10px 30px rgba(15,23,42,0.10)",
} as const;

export const BRAND_GRADIENT = "linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)";
export const SCENE_BG = "linear-gradient(160deg, #faf7ff 0%, #fff1f6 100%)";

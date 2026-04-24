import { ReactNode } from "react";
import { COLORS, ELEVATION, HIGHLIGHT, SCENE_BG, WordTypeColorKey } from "./theme";
import logoUrl from "./assets/contxtly.svg";

export { logoUrl };

export const SCENE_W = 1280;
export const SCENE_H = 800;
export const BLEED_W = 1380;
export const BLEED_H = 900;
export const PROMO_W = 440;
export const PROMO_H = 280;
export const PROMO_BLEED_W = 540;
export const PROMO_BLEED_H = 380;

export function Scene({ title, subtitle, children }: { title: string; subtitle?: string; children: ReactNode }) {
  return (
    <div
      style={{
        width: BLEED_W,
        height: BLEED_H,
        background: SCENE_BG,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Orbs decorate the outer wrapper — positioned to show through the centered 1280×800 capture window */}
      <div style={{ position: "absolute", top: -70, right: -70, width: 420, height: 420, borderRadius: "50%", background: "radial-gradient(circle, rgba(167,139,250,0.35), transparent 60%)", filter: "blur(40px)" }} />
      <div style={{ position: "absolute", bottom: -110, left: -90, width: 460, height: 460, borderRadius: "50%", background: "radial-gradient(circle, rgba(251,113,133,0.25), transparent 60%)", filter: "blur(50px)" }} />
      <div
        style={{
          width: SCENE_W,
          height: SCENE_H,
          background: "transparent",
          position: "relative",
          zIndex: 1,
          display: "grid",
          gridTemplateColumns: "minmax(0, 1fr) minmax(0, 1fr)",
          padding: 64,
          gap: 64,
          alignItems: "center",
        }}
      >
        <div>
          <Caption title={title} subtitle={subtitle} />
        </div>
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center" }}>
          {children}
        </div>
      </div>
    </div>
  );
}

export function Caption({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div style={{ maxWidth: 480 }}>
      <div style={{ display: "inline-flex", alignItems: "center", gap: 8, padding: "6px 12px", background: "rgba(108,0,255,0.08)", color: COLORS.primary.text, borderRadius: 999, fontSize: 12, fontWeight: 700, letterSpacing: 1.2, textTransform: "uppercase", marginBottom: 20 }}>
        <span style={{ width: 6, height: 6, borderRadius: 999, background: COLORS.primary.accent }} /> Contxtly
      </div>
      <h1 style={{ fontSize: 48, lineHeight: 1.08, fontWeight: 800, letterSpacing: -1.2, margin: 0, color: "#0f172a" }}>
        {title}
      </h1>
      {subtitle && (
        <p style={{ fontSize: 18, lineHeight: 1.5, color: "#475569", marginTop: 20, fontWeight: 500 }}>
          {subtitle}
        </p>
      )}
    </div>
  );
}

export function BrowserFrame({ children, url = "spiegel.de/wirtschaft/ki-wettlauf" }: { children: ReactNode; url?: string }) {
  return (
    <div style={{ width: 560, background: "#ffffff", borderRadius: 14, boxShadow: ELEVATION[4], overflow: "hidden", border: "1px solid rgba(15,23,42,0.08)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", background: "#f1f5f9", borderBottom: "1px solid rgba(15,23,42,0.06)" }}>
        <span style={{ width: 10, height: 10, borderRadius: 999, background: "#ff5f57" }} />
        <span style={{ width: 10, height: 10, borderRadius: 999, background: "#febc2e" }} />
        <span style={{ width: 10, height: 10, borderRadius: 999, background: "#28c840" }} />
        <div style={{ flex: 1, marginLeft: 10, background: "#ffffff", borderRadius: 6, padding: "4px 10px", fontSize: 11, color: "#64748b", border: "1px solid rgba(15,23,42,0.06)" }}>
          {url}
        </div>
      </div>
      <div style={{ padding: 28, fontFamily: "'Source Serif 4', Georgia, serif", color: "#1e293b" }}>
        {children}
      </div>
    </div>
  );
}

export function Highlight({ type, children }: { type: WordTypeColorKey; children: ReactNode }) {
  const h = HIGHLIGHT[type];
  return (
    <mark style={{ background: h.bg, boxShadow: h.shadow, borderRadius: 3, padding: "0 2px 1px", color: "inherit" }}>
      {children}
    </mark>
  );
}

export function PopupShell({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        width: 420,
        height: 640,
        background: "linear-gradient(180deg, #ffffff 0%, #faf7ff 100%)",
        borderRadius: 20,
        boxShadow: ELEVATION[4],
        overflow: "hidden",
        border: "1px solid rgba(15,23,42,0.06)",
        display: "flex",
        flexDirection: "column",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      {children}
    </div>
  );
}

export function PopupHeader({ active }: { active: "list" | "review" | "settings" }) {
  const tabs: { key: "list" | "review" | "settings"; label: string }[] = [
    { key: "list", label: "Words" },
    { key: "review", label: "Review" },
    { key: "settings", label: "Settings" },
  ];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 14px", borderBottom: "1px solid #f1f5f9" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <img src={logoUrl} alt="" style={{ width: 26, height: 26, borderRadius: 6, display: "block" }} />
        <span style={{ fontWeight: 800, fontSize: 14, color: "#0f172a" }}>Contxtly</span>
      </div>
      <div style={{ flex: 1 }} />
      <div style={{ display: "flex", gap: 4, background: "#f1f5f9", padding: 3, borderRadius: 10 }}>
        {tabs.map(t => (
          <span
            key={t.key}
            style={{
              fontSize: 11, fontWeight: 700, padding: "5px 10px", borderRadius: 7,
              color: active === t.key ? "#0f172a" : "#64748b",
              background: active === t.key ? "#ffffff" : "transparent",
              boxShadow: active === t.key ? ELEVATION[1] : "none",
            }}
          >
            {t.label}
          </span>
        ))}
      </div>
    </div>
  );
}

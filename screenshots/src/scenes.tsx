import { Volume2, Eye, Search, Settings2, Trash2, Sparkles, CheckCircle2, Globe, Archive } from "lucide-react";
import { BrowserFrame, Highlight, PopupHeader, PopupShell, Scene, PROMO_W, PROMO_H, PROMO_BLEED_W, PROMO_BLEED_H, logoUrl } from "./ui";
import { COLORS, ELEVATION, RADIUS, SCENE_BG } from "./theme";
import { ARTICLE, MOCK_WORDS } from "./data";

// Renders article paragraphs with inline highlights. $WORD$ syntax marks highlighted words.
function ArticleBody({ highlightedMap }: { highlightedMap: Record<string, { type: "verb" | "noun" | "adjective" | "collocation" | "expression" | "compound" }> }) {
  return (
    <>
      <div style={{ fontSize: 11, color: "#64748b", textTransform: "uppercase", letterSpacing: 1.4, fontWeight: 700, fontFamily: "Inter, sans-serif", marginBottom: 10 }}>
        {ARTICLE.source} · {ARTICLE.date}
      </div>
      <h2 style={{ fontSize: 22, lineHeight: 1.25, margin: "0 0 10px", color: "#0f172a", fontWeight: 700 }}>{ARTICLE.headline}</h2>
      <p style={{ fontSize: 13, color: "#475569", margin: "0 0 16px", lineHeight: 1.55 }}>{ARTICLE.subhead}</p>
      {ARTICLE.paragraphs.map((p, i) => (
        <p key={i} style={{ fontSize: 13.5, lineHeight: 1.7, margin: "0 0 12px" }}>
          {renderWithHighlights(p, highlightedMap)}
        </p>
      ))}
    </>
  );
}

function renderWithHighlights(text: string, map: Record<string, { type: any }>) {
  const parts = text.split(/\$([A-ZÄÖÜ\- ]+)\$/g);
  return parts.map((part, i) => {
    if (i % 2 === 1) {
      const key = part;
      const entry = map[key];
      const display = entry ? key.toLowerCase().replace(/(^|\s)\S/g, s => s.toUpperCase()) : part.toLowerCase();
      if (entry) return <Highlight key={i} type={entry.type}>{prettyCase(key)}</Highlight>;
      return <span key={i}>{prettyCase(key)}</span>;
    }
    return <span key={i}>{part}</span>;
  });
}

function prettyCase(k: string) {
  // Keep original casing: GEGENSEITIG → gegenseitig, KI-RENNEN → KI-Rennen, WELTWIRTSCHAFT → Weltwirtschaft, ABHÄNGIGKEITEN → Abhängigkeiten
  const map: Record<string, string> = {
    "SPIELEN": "spielen",
    "ROLLE": "Rolle",
    "TECHNOLOGIEKONZERNE": "Technologiekonzerne",
    "EINZELNE": "einzelne",
    "ABHÄNGIGKEITEN": "Abhängigkeiten",
    "WELTWIRTSCHAFT": "Weltwirtschaft",
  };
  return map[k] ?? k;
}

function CompoundTooltip() {
  const t = COLORS.compound;
  return (
    <div style={{ position: "absolute", top: 55, left: 25, width: 280, background: "#ffffff", borderRadius: 14, border: `1px solid ${t.ring}`, boxShadow: ELEVATION[4], padding: 14, fontFamily: "Inter, sans-serif" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
        <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: 1.4, textTransform: "uppercase", background: t.bg, color: t.text, padding: "3px 8px", borderRadius: 999, border: `1px solid ${t.ring}`, display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span style={{ width: 5, height: 5, borderRadius: 999, background: t.accent }} />
          Compound
        </span>
        <Volume2 size={13} color="#94a3b8" />
      </div>
      <div style={{ fontSize: 18, fontWeight: 800, color: t.text, marginBottom: 2 }}>Technologiekonzerne</div>
      <div style={{ fontSize: 14, fontWeight: 700, color: "#0f172a", marginBottom: 8 }}>tech corporations</div>
      <div style={{ display: "flex", alignItems: "center", gap: 6, padding: "8px 10px", background: t.bg, borderRadius: 10, border: `1px dashed ${t.ring}` }}>
        <div style={{ flex: 1, textAlign: "center" }}>
          <div style={{ fontSize: 12, fontWeight: 800, color: t.text }}>Technologie</div>
          <div style={{ fontSize: 10, color: "#64748b", marginTop: 1 }}>technology</div>
        </div>
        <span style={{ fontSize: 16, color: t.accent, fontWeight: 800 }}>+</span>
        <div style={{ flex: 1, textAlign: "center" }}>
          <div style={{ fontSize: 12, fontWeight: 800, color: t.text }}>Konzerne</div>
          <div style={{ fontSize: 10, color: "#64748b", marginTop: 1 }}>corporations</div>
        </div>
      </div>
    </div>
  );
}

// ── Scene 1: hero — collocation detected across split words ──────────────────
export function Scene1Hero() {
  const t = COLORS.collocation;
  return (
    <Scene
      title="Translate any word, in context, for free."
      subtitle="Contxtly reads the surrounding sentence — it even catches collocations whose parts are separated by other words."
    >
      <div style={{ position: "relative" }}>
        <BrowserFrame>
          <ArticleBody highlightedMap={{ TECHNOLOGIEKONZERNE: { type: "compound" }, SPIELEN: { type: "collocation" }, ROLLE: { type: "collocation" } }} />
        </BrowserFrame>
        {/* Compound tooltip above "Technologiekonzerne" */}
        <CompoundTooltip />
        {/* Tooltip anchored below "Rolle" in paragraph 1 */}
        <div style={{ position: "absolute", top: 310, left: 220, width: 280, background: "#ffffff", borderRadius: 14, border: `1px solid ${t.ring}`, boxShadow: ELEVATION[4], padding: 14, fontFamily: "Inter, sans-serif" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: 1.4, textTransform: "uppercase", background: t.bg, color: t.text, padding: "3px 8px", borderRadius: 999, border: `1px solid ${t.ring}`, display: "inline-flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 5, height: 5, borderRadius: 999, background: t.accent }} />
              Collocation
            </span>
            <Volume2 size={13} color="#94a3b8" />
          </div>
          <div style={{ fontSize: 18, fontWeight: 800, color: t.text, marginBottom: 2 }}>eine Rolle spielen</div>
          <div style={{ fontSize: 14, fontWeight: 700, color: "#0f172a", marginBottom: 6 }}>to play a role</div>
          <div style={{ fontSize: 11.5, color: "#64748b", lineHeight: 1.5, marginBottom: 10 }}>
            A fixed German expression where <em>spielen</em> and <em>Rolle</em> together mean “to play a role” — even when split by an adjective.
          </div>
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 999, background: t.bg, color: t.text, border: `1px solid ${t.ring}` }}>spielen</span>
            <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 999, background: t.bg, color: t.text, border: `1px solid ${t.ring}` }}>+ Rolle</span>
          </div>
        </div>
      </div>
    </Scene>
  );
}

// ── Scene 2: several saved highlights on the page ────────────────────────────
export function Scene2Save() {
  return (
    <Scene
      title="Build your vocabulary as you read."
      subtitle="Save words with one click. They stay highlighted and color-coded on the page — verbs, nouns, expressions, and more."
    >
      <BrowserFrame>
        <ArticleBody
          highlightedMap={{
            SPIELEN: { type: "collocation" },
            ROLLE: { type: "collocation" },
            TECHNOLOGIEKONZERNE: { type: "compound" },
            EINZELNE: { type: "adjective" },
            "ABHÄNGIGKEITEN": { type: "noun" },
            "WELTWIRTSCHAFT": { type: "noun" },
          }}
        />
        <LegendStrip />
      </BrowserFrame>
    </Scene>
  );
}

function LegendStrip() {
  const legend: { type: keyof typeof COLORS; label: string }[] = [
    { type: "verb", label: "Verb" },
    { type: "noun", label: "Noun" },
    { type: "adjective", label: "Adjective" },
    { type: "compound", label: "Compound" },
    { type: "expression", label: "Expression" },
  ];
  return (
    <div style={{ marginTop: 18, paddingTop: 14, borderTop: "1px solid #f1f5f9", display: "flex", gap: 10, flexWrap: "wrap", fontFamily: "Inter, sans-serif" }}>
      {legend.map(l => {
        const c = COLORS[l.type];
        return (
          <span key={l.label} style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 10, fontWeight: 700, color: c.text, background: c.bg, border: `1px solid ${c.ring}`, borderRadius: 999, padding: "3px 10px", textTransform: "uppercase", letterSpacing: 0.6 }}>
            <span style={{ width: 6, height: 6, borderRadius: 999, background: c.accent }} /> {l.label}
          </span>
        );
      })}
    </div>
  );
}

// ── Scene 3: popup in review mode ────────────────────────────────────────────
export function Scene3Review() {
  const t = COLORS.collocation;
  return (
    <Scene
      title="Review with spaced repetition."
      subtitle="Come back to saved words on a proven schedule. See each word in the sentence you learned it from — with the word bolded in context."
    >
      <PopupShell>
        <PopupHeader active="review" />
        <div style={{ padding: "14px 14px 12px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8, fontSize: 10, fontWeight: 800, color: "#64748b", letterSpacing: 1.4, textTransform: "uppercase" }}>
            <span>1 of 29 due</span>
          </div>
          <div style={{ height: 4, borderRadius: 999, background: "#f1f5f9", overflow: "hidden", marginBottom: 14 }}>
            <div style={{ width: "12%", height: "100%", background: COLORS.primary.accent }} />
          </div>
          <div style={{ borderRadius: RADIUS.xl, background: `linear-gradient(160deg, ${t.bg}, #ffffff)`, border: `1px solid ${t.ring}`, boxShadow: ELEVATION[2], padding: 18, minHeight: 380, display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 9, fontWeight: 800, letterSpacing: 1.4, textTransform: "uppercase", background: t.bg, color: t.text, padding: "3px 8px", borderRadius: 999, border: `1px solid ${t.ring}`, display: "inline-flex", alignItems: "center", gap: 6 }}>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: t.accent }} />
                Collocation
              </span>
              <Volume2 size={14} color="#94a3b8" />
            </div>
            <div style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", textAlign: "center", padding: "16px 8px" }}>
              <h2 style={{ fontSize: 26, fontWeight: 800, color: t.text, margin: 0, letterSpacing: -0.4 }}>eine Rolle spielen</h2>
              <p style={{ fontSize: 12.5, fontStyle: "italic", color: "#64748b", lineHeight: 1.55, maxWidth: 300, margin: "10px 0 16px" }}>
                "Anthropic, Microsoft und Google <span style={{ fontWeight: 800, color: "#334155" }}>spielen</span> beim KI-Rennen eine entscheidende <span style={{ fontWeight: 800, color: "#334155" }}>Rolle</span>."
              </p>
              <p style={{ fontSize: 17, fontWeight: 800, color: t.text, margin: "4px 0 6px" }}>to play a role</p>
              <p style={{ fontSize: 12, color: "#64748b", lineHeight: 1.55, maxWidth: 300, margin: 0 }}>
                Contxtly detected the collocation even though "spielen" and "Rolle" were split by several words.
              </p>
            </div>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10, marginTop: 18 }}>
            {[
              { l: "Again", h: "<1m", c: "#fef2f2", tx: "#b91c1c" },
              { l: "Hard", h: "1d", c: "#fffbeb", tx: "#92400e" },
              { l: "Good", h: "3d", c: "#eef2ff", tx: "#4338ca" },
              { l: "Easy", h: "6d", c: "#ecfdf5", tx: "#065f46" },
            ].map(g => (
              <div key={g.l} style={{ background: g.c, color: g.tx, borderRadius: RADIUS.md, border: `1px solid ${g.tx}22`, padding: "8px 0", display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span style={{ fontSize: 12, fontWeight: 800 }}>{g.l}</span>
                <span style={{ fontSize: 9, fontWeight: 500, opacity: 0.7, marginTop: 2 }}>{g.h}</span>
              </div>
            ))}
          </div>
        </div>
      </PopupShell>
    </Scene>
  );
}

// ── Scene 4: popup word list ─────────────────────────────────────────────────
export function Scene4List() {
  return (
    <Scene
      title="Every word, at your fingertips."
      subtitle="Browse everything you've saved, organized by type. Pronounce, export to Anki, or remove in a tap."
    >
      <PopupShell>
        <PopupHeader active="list" />
        <div style={{ padding: "12px 14px 10px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, background: "#f8fafc", border: "1px solid #e2e8f0", borderRadius: 10, padding: "8px 10px" }}>
            <Search size={14} color="#94a3b8" />
            <span style={{ fontSize: 12, color: "#94a3b8" }}>Search your words…</span>
          </div>
          <div style={{ display: "flex", gap: 6, marginTop: 10, overflowX: "auto", paddingBottom: 2 }}>
            {["All", "Verb", "Noun", "Adjective", "Compound", "Expression"].map((f, i) => (
              <span key={f} style={{ fontSize: 10, fontWeight: 700, padding: "5px 10px", borderRadius: 999, border: "1px solid #e2e8f0", background: i === 0 ? "#0f172a" : "#ffffff", color: i === 0 ? "#ffffff" : "#475569", whiteSpace: "nowrap" }}>
                {f}
              </span>
            ))}
          </div>
        </div>
        <div style={{ flex: 1, overflow: "hidden", padding: "0 14px 14px", display: "flex", flexDirection: "column", gap: 12 }}>
          {MOCK_WORDS.slice(0, 6).map(w => {
            const c = COLORS[w.type];
            return (
              <div key={w.text} style={{ borderRadius: 14, background: `linear-gradient(160deg, ${c.bg}, #ffffff)`, border: `1px solid ${c.ring}`, padding: "10px 12px", boxShadow: ELEVATION[1] }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontSize: 14, fontWeight: 800, color: c.text }}>{w.text}</span>
                  <span style={{ fontSize: 8, fontWeight: 800, letterSpacing: 1.2, textTransform: "uppercase", background: "#ffffff", color: c.text, padding: "2px 7px", borderRadius: 999, border: `1px solid ${c.ring}` }}>
                    {w.type}
                  </span>
                  <div style={{ flex: 1 }} />
                  <span style={{ fontSize: 10, color: "#94a3b8" }}>{w.savedAgo}</span>
                </div>
                <div style={{ fontSize: 12, color: "#475569", marginTop: 3, fontWeight: 600 }}>{w.translation}</div>
              </div>
            );
          })}
        </div>
        <div style={{ padding: "8px 14px", borderTop: "1px solid #f1f5f9", display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 6, height: 6, borderRadius: 999, background: "#94a3b8" }} />
          <span style={{ fontSize: 10.5, color: "#64748b", fontWeight: 600 }}>29 words saved</span>
          <div style={{ flex: 1 }} />
          <span style={{ fontSize: 10.5, color: COLORS.primary.text, fontWeight: 700 }}>Export to Anki</span>
        </div>
      </PopupShell>
    </Scene>
  );
}

// ── Scene 5: settings / language selection ───────────────────────────────────
export function Scene5Settings() {
  return (
    <Scene
      title="Made for real language learners."
      subtitle="Works on any website, in any language. Syncs across devices. Optional Anki integration for the power users."
    >
      <PopupShell>
        <PopupHeader active="settings" />
        <div style={{ padding: 16, display: "flex", flexDirection: "column", gap: 14 }}>
          <SettingsRow icon={<Globe size={14} />} label="Learning language" value="German" />
          <SettingsRow icon={<Globe size={14} />} label="Translate into" value="English" />
          <SettingsRow icon={<CheckCircle2 size={14} color="#10b981" />} label="Extension enabled" toggle />
          <SettingsRow icon={<Sparkles size={14} />} label="Show word of the day" toggle />
          <SettingsRow icon={<Archive size={14} />} label="Auto-sync to Anki" toggle on />
          <SettingsRow icon={<Settings2 size={14} />} label="Keyboard shortcuts" value="⌘ ⇧ K" />
          <SettingsRow icon={<Trash2 size={14} color="#ef4444" />} label="Clear all saved words" value="" danger />
        </div>
        <div style={{ marginTop: "auto", padding: 14, borderTop: "1px solid #f1f5f9", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 999, background: "linear-gradient(135deg,#8b5cf6,#ec4899)" }} />
          <div>
            <div style={{ fontSize: 12, fontWeight: 700, color: "#0f172a" }}>Clara R.</div>
            <div style={{ fontSize: 10, color: "#64748b" }}>Pro · synced 2m ago</div>
          </div>
        </div>
      </PopupShell>
    </Scene>
  );
}

function SettingsRow({ icon, label, value, toggle, on, danger }: { icon: React.ReactNode; label: string; value?: string; toggle?: boolean; on?: boolean; danger?: boolean }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 12px", background: "#ffffff", border: "1px solid #e2e8f0", borderRadius: 12 }}>
      <div style={{ width: 28, height: 28, borderRadius: 8, background: "#f8fafc", display: "flex", alignItems: "center", justifyContent: "center", color: "#475569" }}>
        {icon}
      </div>
      <span style={{ fontSize: 12.5, fontWeight: 600, color: danger ? "#ef4444" : "#0f172a" }}>{label}</span>
      <div style={{ flex: 1 }} />
      {toggle ? (
        <div style={{ width: 32, height: 18, borderRadius: 999, background: on === false ? "#e2e8f0" : COLORS.primary.accent, position: "relative", transition: "background 0.2s" }}>
          <div style={{ position: "absolute", top: 2, left: on === false ? 2 : 16, width: 14, height: 14, borderRadius: 999, background: "#ffffff", boxShadow: ELEVATION[1] }} />
        </div>
      ) : (
        <span style={{ fontSize: 11.5, fontWeight: 600, color: "#64748b" }}>{value}</span>
      )}
    </div>
  );
}

// ── Promo tile 440×280 ───────────────────────────────────────────────────────
export function PromoTile() {
  return (
    <div
      style={{
        width: PROMO_BLEED_W,
        height: PROMO_BLEED_H,
        background: SCENE_BG,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
        overflow: "hidden",
      }}
    >
      <div style={{ position: "absolute", top: -40, right: -40, width: 220, height: 220, borderRadius: "50%", background: "radial-gradient(circle, rgba(167,139,250,0.4), transparent 60%)", filter: "blur(30px)" }} />
      <div style={{ position: "absolute", bottom: -60, left: -50, width: 240, height: 240, borderRadius: "50%", background: "radial-gradient(circle, rgba(251,113,133,0.3), transparent 60%)", filter: "blur(35px)" }} />
      <div
        style={{
          width: PROMO_W,
          height: PROMO_H,
          background: "transparent",
          position: "relative",
          zIndex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 18,
          padding: 32,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <img src={logoUrl} alt="Contxtly logo" style={{ width: 110, height: 110, display: "block", filter: "drop-shadow(0 8px 24px rgba(91,33,182,0.25))" }} />
          <div style={{ fontFamily: "Inter, sans-serif", fontSize: 58, fontWeight: 800, letterSpacing: -1.8, color: "#0f172a", lineHeight: 1 }}>
            Contxtly
          </div>
        </div>
        <div style={{ fontFamily: "Inter, sans-serif", fontSize: 15, fontWeight: 600, color: "#475569", letterSpacing: -0.2 }}>
          Translate any word — in context.
        </div>
      </div>
    </div>
  );
}

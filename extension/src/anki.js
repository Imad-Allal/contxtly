const ANKI_URL = "http://localhost:8765";
const ANKI_DECK = "Contxtly";

// ── Card styling ─────────────────────────────────────────────────────────────

const FONT = "'DM Sans',sans-serif";
const FONT_URL = "https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap";

const LABEL_COLORS = {
  Translation: "#6ee7b7",
  Meaning:     "#93c5fd",
  Breakdown:   "#f9a8d4",
  Context:     "#fcd34d",
};

function cardSection(label, value) {
  const color = LABEL_COLORS[label] ?? "#fff";
  return `
    <div style="margin-bottom:22px">
      <div style="font-size:9px;letter-spacing:0.18em;text-transform:uppercase;color:${color};font-family:${FONT};font-weight:600;margin-bottom:7px">${label}</div>
      <div style="font-size:16px;color:#fff;line-height:1.6;font-family:${FONT};font-weight:400">${value}</div>
    </div>`;
}

const DIVIDER = `<div style="height:1px;background:linear-gradient(90deg,transparent,#555,transparent);margin:2px 0 22px"></div>`;

function buildCardBack(h) {
  const raw = h.translation;
  const t = typeof raw === "object" && raw !== null ? raw : {};

  if (typeof raw === "string") {
    return cardSection("Translation", raw);
  }

  let html = "";

  if (t.translation) {
    html += cardSection("Translation", `<span style="font-weight:500">${t.translation}</span>`);
  }
  if (t.meaning) {
    html += DIVIDER;
    html += cardSection("Meaning", `<span style="color:#e2e8f0;font-style:italic">${t.meaning}</span>`);
  }
  if (t.breakdown) {
    const styled = t.breakdown.replace(/\(([^)]+)\)/g, `<span style="color:#cbd5e1;font-size:0.88em">($1)</span>`);
    html += DIVIDER;
    html += cardSection("Breakdown", styled);
  }

  const source = t.context_translation?.source;
  const target = t.context_translation?.target;
  const url = h.url;
  if (source || target || url) {
    const ctx = `
      <div style="border-left:2px solid #777;padding-left:14px;display:flex;flex-direction:column;gap:10px">
        ${source ? `<div style="color:#e2e8f0;font-size:13px;font-family:${FONT};font-style:italic">${source}</div>` : ""}
        ${target ? `<div style="color:#fff;font-size:13px;font-family:${FONT}">${target}</div>` : ""}
        ${url ? `<a href="${url}" style="color:#93c5fd;font-size:11px;font-family:${FONT};word-break:break-all;text-decoration:none">${url}</a>` : ""}
      </div>`;
    html += DIVIDER;
    html += cardSection("Context", ctx);
  }

  return `<link href="${FONT_URL}" rel="stylesheet"><div style="font-family:${FONT};padding:8px 4px">${html}</div>`;
}

// ── AnkiConnect ───────────────────────────────────────────────────────────────

async function ankiRequest(action, params) {
  const r = await fetch(ANKI_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, version: 6, params }),
  });
  return r.json();
}

// Pick the best Basic-style model generically:
// 1. Prefer any model whose name contains "basic" (case-insensitive, any language)
// 2. Otherwise prefer the model with exactly 2 fields
// 3. Exclude cloze/image/occlusion types (they have special fields, not Front/Back)
// 4. Fall back to the first available model
async function resolveAnkiModel() {
  const { result: models = [] } = await ankiRequest("modelNames", {});

  // Fetch field counts for all models in parallel
  const fieldResults = await Promise.all(
    models.map((m) => ankiRequest("modelFieldNames", { modelName: m }))
  );

  const candidates = models.map((m, i) => ({
    name: m,
    fields: fieldResults[i].result || [],
  }));

  // Score each candidate (higher = better)
  function score(c) {
    const name = c.name.toLowerCase();
    // Exclude special types
    if (/cloze|occlusion|image|bild|lück/i.test(name)) return -1;
    // Exact 2-field model named "basic" in any language is ideal
    if (/basic|einfach|basique|básico|simpel|base|simpl/i.test(name) && c.fields.length === 2) return 3;
    // Any "basic"-named model
    if (/basic|einfach|basique|básico|simpel|base|simpl/i.test(name)) return 2;
    // Any 2-field model
    if (c.fields.length === 2) return 1;
    return 0;
  }

  const best = candidates
    .filter((c) => score(c) >= 0)
    .sort((a, b) => score(b) - score(a))[0] || candidates[0];

  return {
    modelName: best.name,
    frontField: best.fields[0] || "Front",
    backField: best.fields[1] || "Back",
  };
}

// ── Export handler ────────────────────────────────────────────────────────────

export async function handleExportToAnki() {
  const { highlights = {} } = await chrome.storage.local.get(["highlights"]);

  const seen = new Set();
  const words = Object.entries(highlights)
    .flatMap(([url, items]) => items.map((h) => ({ ...h, url })))
    .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
    .filter((h) => {
      const key = h.lemma || h.text;
      return !seen.has(key) && seen.add(key);
    });

  if (!words.length) return { added: 0, duplicates: 0, errors: 0, empty: true };

  await ankiRequest("createDeck", { deck: ANKI_DECK });
  const { modelName, frontField, backField } = await resolveAnkiModel();

  const notes = words.map((h) => {
    const lemma = h.lemma || h.text;
    const front = h.text !== lemma ? `${h.text} (${lemma})` : lemma;
    return {
      deckName: ANKI_DECK,
      modelName,
      fields: { [frontField]: front, [backField]: buildCardBack(h) },
      tags: ["contxtly"],
      options: { allowDuplicate: false },
    };
  });

  const { result } = await ankiRequest("addNotes", { notes });
  const results = Array.isArray(result) ? result : [];
  return {
    added: results.filter((id) => id !== null).length,
    duplicates: results.filter((id) => id === null).length,
    errors: notes.length - results.length,
  };
}

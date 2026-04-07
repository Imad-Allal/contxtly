let button = null;
let tooltip = null;

const ICONS = {
  delete: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>`,
};

// ── Type system ──────────────────────────────────────────────────────────────

const TYPE_INFO = {
  conjugated_verb:  { cls: "contxtly-verb",        label: "Verb" },
  separable_prefix: { cls: "contxtly-verb",        label: "Sep. Verb" },
  collocation_verb: { cls: "contxtly-collocation", label: "Collocation" },
  collocation_prep: { cls: "contxtly-collocation", label: "Collocation" },
  noun:             { cls: "contxtly-noun",        label: "Noun" },
  plural_noun:      { cls: "contxtly-noun",        label: "Noun" },
  adjective:        { cls: "contxtly-adjective",   label: "Adjective" },
  fixed_expression: { cls: "contxtly-expression",  label: "Expression" },
  compound:         { cls: "contxtly-compound",    label: "Compound" },
};

function getTypeInfo(translation) {
  if (!translation || typeof translation !== "object") return null;
  // Use explicit word_type first
  if (translation.word_type && TYPE_INFO[translation.word_type]) {
    return TYPE_INFO[translation.word_type];
  }
  // Fallback inference from available fields
  if (translation.collocation_pattern) {
    return TYPE_INFO.collocation_verb;
  }
  return null;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function clamp(x, y, w, h) {
  return {
    x: Math.max(10, Math.min(x, window.innerWidth - w - 10)),
    y: Math.max(10, Math.min(y, window.innerHeight - h - 10)),
  };
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function isSimpleTranslation(data) {
  if (typeof data === "string") return true;
  if (typeof data === "object" && data !== null) {
    return data.translation && !data.meaning && !data.breakdown && !data.context_translation;
  }
  return false;
}

function formatTranslation(data) {
  if (typeof data === "string") {
    return `<div class="contxtly-simple-translation">${escapeHtml(data)}</div>`;
  }

  if (typeof data === "object" && data !== null) {
    if (isSimpleTranslation(data)) {
      return `<div class="contxtly-simple-translation">${escapeHtml(data.translation)}</div>`;
    }

    let html = "";

    // Type badge
    const info = getTypeInfo(data);
    if (info) {
      html += `<div class="contxtly-type-badge ${info.cls}-badge">${info.label}</div>`;
    }

    if (data.translation) {
      html += `<div class="contxtly-section contxtly-translation">${escapeHtml(data.translation)}</div>`;
    }
    if (data.meaning) {
      html += `<div class="contxtly-section contxtly-meaning">${escapeHtml(data.meaning)}</div>`;
    }
    if (data.breakdown) {
      html += `<div class="contxtly-section contxtly-breakdown">${escapeHtml(data.breakdown)}</div>`;
    }
    if (data.context_translation?.source) {
      const boldTerm = (text, term) => {
        if (!term) return escapeHtml(text);
        const escapedText = escapeHtml(text);
        const escapedTerm = escapeHtml(term).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
        return escapedText.replace(new RegExp(`(${escapedTerm})`, 'gi'), '<strong>$1</strong>');
      };

      html += `<div class="contxtly-section contxtly-context-translation">
        <div class="contxtly-context-translation-source">${boldTerm(data.context_translation.source, data.lemma)}</div>
        <div class="contxtly-context-translation-target">${boldTerm(data.context_translation.target, data.translation)}</div>
      </div>`;
    }

    return html || escapeHtml(JSON.stringify(data));
  }

  return "";
}

function setPosition(el, x, y, w, h) {
  const scrollX = window.pageXOffset || document.documentElement.scrollLeft;
  const scrollY = window.pageYOffset || document.documentElement.scrollTop;
  const pos = clamp(x, y + 10, w, h);
  el.style.left = `${pos.x + scrollX}px`;
  el.style.top = `${pos.y + scrollY}px`;
}

function buildTypeClasses(content) {
  const info = getTypeInfo(typeof content === "object" ? content : null);
  return info ? ` ${info.cls}` : "";
}

// ── Button ───────────────────────────────────────────────────────────────────

export function showButton(x, y, onClick) {
  removeButton();
  button = document.createElement("button");
  button.className = "contxtly-btn";
  button.textContent = "Translate";
  setPosition(button, x, y, 100, 36);

  button.onclick = (e) => {
    e.stopPropagation();
    onClick();
    removeButton();
  };

  document.body.appendChild(button);
}

export function removeButton() {
  button?.remove();
  button = null;
}

// ── Tooltip ──────────────────────────────────────────────────────────────────

export function showTooltip(x, y) {
  removeTooltip();
  tooltip = document.createElement("div");
  tooltip.className = "contxtly-tooltip contxtly-tooltip-loading";
  tooltip.textContent = "Translating…";
  setPosition(tooltip, x, y, 320, 100);
  document.body.appendChild(tooltip);
}

export function updateTooltip(content, isError = false, onDelete = null) {
  if (!tooltip) return;
  const simpleClass = isSimpleTranslation(content) ? " contxtly-tooltip-simple" : "";
  const typeClass = buildTypeClasses(content);
  tooltip.className = `contxtly-tooltip${isError ? " contxtly-tooltip-error" : ""}${simpleClass}${typeClass}`;
  tooltip.innerHTML = isError ? escapeHtml(content) : formatTranslation(content);

  if (!isError && onDelete) {
    const btn = document.createElement("button");
    btn.className = "contxtly-tooltip-delete";
    btn.innerHTML = ICONS.delete;
    btn.onclick = (e) => {
      e.stopPropagation();
      onDelete();
      removeTooltip();
    };
    tooltip.appendChild(btn);
  }
}

export function removeTooltip() {
  tooltip?.remove();
  tooltip = null;
}

export function updateTooltipLogin() {
  if (!tooltip) return;
  tooltip.className = "contxtly-tooltip contxtly-tooltip-auth";
  tooltip.innerHTML = `
    <div class="contxtly-auth-msg">
      <span>Sign in to translate</span>
      <button class="contxtly-auth-btn" id="contxtly-login-btn">Sign in with Google</button>
    </div>`;
  tooltip.querySelector("#contxtly-login-btn").onclick = (e) => {
    e.stopPropagation();
    chrome.runtime.sendMessage({ action: "login" });
    removeTooltip();
  };
}

export function updateTooltipLimitReached() {
  if (!tooltip) return;
  tooltip.className = "contxtly-tooltip contxtly-tooltip-limit";
  tooltip.innerHTML = `
    <div class="contxtly-auth-msg">
      <span>Daily limit reached</span>
      <button class="contxtly-auth-btn contxtly-upgrade-btn" id="contxtly-upgrade-btn">Upgrade</button>
    </div>`;
  tooltip.querySelector("#contxtly-upgrade-btn").onclick = (e) => {
    e.stopPropagation();
    chrome.runtime.sendMessage({ action: "getCheckoutUrl" }).then((res) => {
      if (res?.url) chrome.runtime.sendMessage({ action: "openUrl", url: res.url });
    });
    removeTooltip();
  };
}

export function showTranslationTooltip(x, y, content, onDelete) {
  removeTooltip();
  tooltip = document.createElement("div");
  const simpleClass = isSimpleTranslation(content) ? " contxtly-tooltip-simple" : "";
  const typeClass = buildTypeClasses(content);
  tooltip.className = `contxtly-tooltip${simpleClass}${typeClass}`;
  tooltip.innerHTML = formatTranslation(content);

  if (onDelete) {
    const btn = document.createElement("button");
    btn.className = "contxtly-tooltip-delete";
    btn.innerHTML = ICONS.delete;
    btn.onclick = (e) => {
      e.stopPropagation();
      onDelete();
      removeTooltip();
    };
    tooltip.appendChild(btn);
  }

  setPosition(tooltip, x, y, 320, 100);
  document.body.appendChild(tooltip);
}

export function isOwnElement(el) {
  return button?.contains(el) || tooltip?.contains(el) || el.classList?.contains("contxtly-highlight");
}

// ── Mark factory (used by highlight.js) ─────────────────────────────────────

const HIGHLIGHT_COLORS = {
  "":                     { bg: "rgba(254,249,195,0.55)", bgHover: "rgba(254,249,195,0.85)", shadow: "inset 0 -2px 0 rgba(234,179,8,0.55)",    shadowHover: "inset 0 -2px 0 rgba(234,179,8,0.85)" },
  "contxtly-verb":        { bg: "rgba(219,234,254,0.45)", bgHover: "rgba(219,234,254,0.75)", shadow: "inset 0 -2px 0 rgba(96,165,250,0.55)",   shadowHover: "inset 0 -2px 0 rgba(96,165,250,0.85)" },
  "contxtly-noun":        { bg: "rgba(237,233,254,0.45)", bgHover: "rgba(237,233,254,0.75)", shadow: "inset 0 -2px 0 rgba(167,139,250,0.55)",  shadowHover: "inset 0 -2px 0 rgba(167,139,250,0.85)" },
  "contxtly-adjective":   { bg: "rgba(254,243,199,0.45)", bgHover: "rgba(254,243,199,0.75)", shadow: "inset 0 -2px 0 rgba(245,158,11,0.55)",   shadowHover: "inset 0 -2px 0 rgba(245,158,11,0.85)" },
  "contxtly-collocation": { bg: "rgba(187,0,81,0.1)",     bgHover: "rgba(187,0,81,0.18)",   shadow: "inset 0 -2px 0 rgba(187,0,81,0.55)",     shadowHover: "inset 0 -2px 0 rgba(187,0,81,0.85)" },
  "contxtly-expression":  { bg: "rgba(255,228,230,0.45)", bgHover: "rgba(255,228,230,0.75)", shadow: "inset 0 -2px 0 rgba(251,113,133,0.55)",  shadowHover: "inset 0 -2px 0 rgba(251,113,133,0.85)" },
  "contxtly-compound":    { bg: "rgba(209,250,229,0.45)", bgHover: "rgba(209,250,229,0.75)", shadow: "inset 0 -2px 0 rgba(52,211,153,0.55)",   shadowHover: "inset 0 -2px 0 rgba(52,211,153,0.85)" },
};

export function getHighlightTypeClass(translation) {
  const info = getTypeInfo(typeof translation === "object" ? translation : null);
  return info ? info.cls : "";
}

export function applyHighlightStyle(el, typeClass) {
  const c = HIGHLIGHT_COLORS[typeClass || ""] || HIGHLIGHT_COLORS[""];
  // Inline styles override page CSS and UA stylesheet on <mark> elements
  el.style.background = c.bg;
  el.style.boxShadow = c.shadow;
  el.style.borderRadius = "3px";
  el.style.padding = "0 2px 1px";
  el.style.cursor = "pointer";
  el.style.webkitBoxDecorationBreak = "clone";
  el.style.boxDecorationBreak = "clone";
  el.style.color = "inherit";
  // Hover via JS events (inline styles block CSS :hover)
  el.addEventListener("mouseenter", () => {
    el.style.background = c.bgHover;
    el.style.boxShadow = c.shadowHover;
  });
  el.addEventListener("mouseleave", () => {
    el.style.background = c.bg;
    el.style.boxShadow = c.shadow;
  });
}

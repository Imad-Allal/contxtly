let button = null;
let tooltip = null;

const ICONS = {
  delete: `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>`,
};

// Helpers
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

function parseTranslation(text) {
  const sections = { Translation: "", Meaning: "", Breakdown: "", Example: "" };
  let current = null;

  for (const line of text.split("\n")) {
    const match = line.match(/^\*\*(\w+)\*\*:\s*(.*)$/);
    if (match && sections.hasOwnProperty(match[1])) {
      current = match[1];
      sections[current] = match[2];
    } else if (current === "Example" && line.trim().startsWith("-")) {
      sections.Example += line.trim() + "\n";
    } else if (current && line.trim()) {
      sections[current] += " " + line.trim();
    }
  }

  return sections;
}

function formatTranslation(text) {
  const s = parseTranslation(text);
  let html = "";

  if (s.Translation) {
    html += `<div class="contxtly-section contxtly-translation">${escapeHtml(s.Translation.trim())}</div>`;
  }
  if (s.Meaning) {
    html += `<div class="contxtly-section contxtly-meaning">${escapeHtml(s.Meaning.trim())}</div>`;
  }
  if (s.Breakdown && /\(.+\)\s*[+=]|[+=]\s*\(.+\)/.test(s.Breakdown)) {
    html += `<div class="contxtly-section contxtly-breakdown">${escapeHtml(s.Breakdown.trim())}</div>`;
  }
  if (s.Example) {
    const lines = s.Example.trim().split("\n").filter(Boolean).map((l) => escapeHtml(l.replace(/^-\s*/, "")));
    if (lines.length >= 2) {
      html += `<div class="contxtly-section contxtly-example">
        <div class="contxtly-example-source">${lines[0]}</div>
        <div class="contxtly-example-translation">${lines[1]}</div>
      </div>`;
    } else if (lines.length) {
      html += `<div class="contxtly-section contxtly-example">${lines[0]}</div>`;
    }
  }

  return html || escapeHtml(text);
}

function setPosition(el, x, y, w, h) {
  const pos = clamp(x, y + 10, w, h);
  el.style.left = `${pos.x}px`;
  el.style.top = `${pos.y}px`;
}

// Button
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

// Tooltip
export function showTooltip(x, y) {
  removeTooltip();
  tooltip = document.createElement("div");
  tooltip.className = "contxtly-tooltip contxtly-tooltip-loading";
  tooltip.textContent = "Translating...";
  setPosition(tooltip, x, y, 320, 100);
  document.body.appendChild(tooltip);
}

export function updateTooltip(content, isError = false) {
  if (!tooltip) return;
  tooltip.className = `contxtly-tooltip${isError ? " contxtly-tooltip-error" : ""}`;
  tooltip.innerHTML = isError ? escapeHtml(content) : formatTranslation(content);
}

export function removeTooltip() {
  tooltip?.remove();
  tooltip = null;
}

export function showTranslationTooltip(x, y, content, onDelete) {
  removeTooltip();
  tooltip = document.createElement("div");
  tooltip.className = "contxtly-tooltip";
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

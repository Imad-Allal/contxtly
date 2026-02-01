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

function isSimpleTranslation(data) {
  if (typeof data === "string") return true;
  if (typeof data === "object" && data !== null) {
    // Simple if only has translation field (no meaning, breakdown, or context_translation)
    return data.translation && !data.meaning && !data.breakdown && !data.context_translation;
  }
  return false;
}

function formatTranslation(data) {
  // Handle string (simple translation)
  if (typeof data === "string") {
    return `<div class="contxtly-simple-translation">${escapeHtml(data)}</div>`;
  }

  // Handle JSON object
  if (typeof data === "object" && data !== null) {
    // Simple translation - object with only translation field
    if (isSimpleTranslation(data)) {
      return `<div class="contxtly-simple-translation">${escapeHtml(data.translation)}</div>`;
    }

    // Smart translation - multiple fields
    let html = "";

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
      html += `<div class="contxtly-section contxtly-context-translation">
        <div class="contxtly-context-translation-source">${escapeHtml(data.context_translation.source)}</div>
        <div class="contxtly-context-translation-target">${escapeHtml(data.context_translation.target)}</div>
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

export function updateTooltip(content, isError = false, onDelete = null) {
  if (!tooltip) return;
  const simpleClass = isSimpleTranslation(content) ? " contxtly-tooltip-simple" : "";
  tooltip.className = `contxtly-tooltip${isError ? " contxtly-tooltip-error" : ""}${simpleClass}`;
  tooltip.innerHTML = isError ? escapeHtml(content) : formatTranslation(content);

  // Add delete button if onDelete callback is provided
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

export function showTranslationTooltip(x, y, content, onDelete) {
  removeTooltip();
  tooltip = document.createElement("div");
  const simpleClass = isSimpleTranslation(content) ? " contxtly-tooltip-simple" : "";
  tooltip.className = `contxtly-tooltip${simpleClass}`;
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

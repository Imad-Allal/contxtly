import { showTranslationTooltip, removeTooltip } from "./ui.js";

const CLASS = "contxtly-highlight";
const SKIP = `.${CLASS}, .contxtly-btn, .contxtly-tooltip`;

const getUrl = () => new URL(location.href).origin + new URL(location.href).pathname;

// Storage
async function getHighlights() {
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  return highlights[getUrl()] || [];
}

async function saveHighlight(text, translation, context) {
  const url = getUrl();
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  if (!highlights[url]) highlights[url] = [];
  highlights[url].push({ text, translation, context, timestamp: Date.now() });
  await chrome.storage.local.set({ highlights });
}

export async function removeFromStorage(text) {
  const url = getUrl();
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  if (!highlights[url]) return;
  highlights[url] = highlights[url].filter((h) => h.text !== text);
  if (!highlights[url].length) delete highlights[url];
  await chrome.storage.local.set({ highlights });
}

export async function getCachedTranslation(text, context) {
  const found = (await getHighlights()).find((h) => h.text === text && h.context === context);
  return found?.translation || null;
}

// DOM helpers
function unwrap(el) {
  const parent = el.parentNode;
  while (el.firstChild) parent.insertBefore(el.firstChild, el);
  parent.removeChild(el);
  parent.normalize();
}

// Remove all highlights for a given text
export function removeHighlightFromDOM(text) {
  document.querySelectorAll('.contxtly-highlight').forEach((mark) => {
    if (mark.textContent === text) unwrap(mark);
  });
}

// Create delete handler for a highlighted word
function createDeleteHandler(text) {
  return async () => {
    await removeFromStorage(text);
    removeHighlightFromDOM(text);
  };
}

function createMark(translation, text) {
  const mark = document.createElement("mark");
  mark.className = CLASS;
  // Store as JSON string for dataset
  mark.dataset.translation = typeof translation === "object" ? JSON.stringify(translation) : translation;

  mark.onclick = (e) => {
    e.stopPropagation();
    const rect = mark.getBoundingClientRect();
    // Parse back if needed
    let data = mark.dataset.translation;
    try { data = JSON.parse(data); } catch {}
    showTranslationTooltip(rect.left, rect.bottom, data, createDeleteHandler(text || mark.textContent));
  };

  return mark;
}

function getContext(range, text) {
  const el = range.commonAncestorContainer;
  const block = (el.nodeType === Node.TEXT_NODE ? el.parentElement : el)?.closest("p, div, li, td, article, section");
  const full = block?.textContent || "";
  const idx = full.indexOf(text);
  if (idx === -1) return "";
  return full.slice(Math.max(0, idx - 30), Math.min(full.length, idx + text.length + 30));
}

// Highlight selection
export async function highlightSelection(range, text, translation) {
  if (!range) return;

  const container = range.commonAncestorContainer;
  const parent = container.nodeType === Node.TEXT_NODE ? container.parentElement : container;
  const existing = parent?.closest?.(`.${CLASS}`);

  if (existing?.textContent === text) return;

  // Unwrap overlapping highlights
  if (existing || parent?.querySelector?.(`.${CLASS}`)) {
    const root = parent?.closest("p, div, li, td, article, section") || document.body;
    for (const mark of root.querySelectorAll(`.${CLASS}`)) {
      try {
        const r = document.createRange();
        r.selectNode(mark);
        if (range.compareBoundaryPoints(Range.END_TO_START, r) <= 0 &&
            range.compareBoundaryPoints(Range.START_TO_END, r) >= 0) {
          unwrap(mark);
        }
      } catch {}
    }
  }

  const context = getContext(range, text);

  try {
    range.surroundContents(createMark(translation, text));
  } catch {
    try {
      const contents = range.extractContents();
      contents.querySelectorAll?.(`.${CLASS}`).forEach(unwrap);
      const mark = createMark(translation, text);
      mark.appendChild(contents);
      range.insertNode(mark);
    } catch {}
  }

  await saveHighlight(text, translation, context);
}

// Restore on page load
function restoreHighlight(text, translation, context) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT :
                       n.textContent.includes(text) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
  });

  while (walker.nextNode()) {
    const node = walker.currentNode;
    const idx = node.textContent.indexOf(text);
    if (idx === -1) continue;

    const block = node.parentElement?.closest("p, div, li, td, article, section");
    if (context && !block?.textContent?.includes(context.slice(10, -10))) continue;

    try {
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + text.length);
      range.surroundContents(createMark(translation, text));
      return;
    } catch {}
  }
}

async function restore() {
  for (const { text, translation, context } of await getHighlights()) {
    restoreHighlight(text, translation, context || "");
  }
}

// Message listener
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "removeHighlight") {
    document.querySelectorAll(`.${CLASS}`).forEach((m) => m.textContent === msg.text && unwrap(m));
  }
});

// Close tooltip on outside click
document.addEventListener("click", (e) => {
  if (!e.target.closest(`.${CLASS}`) && !e.target.closest(".contxtly-tooltip")) {
    removeTooltip();
  }
});

restore();

import { showTranslationTooltip, removeTooltip } from "./ui.js";

const CLASS = "contxtly-highlight";
const SKIP = `.${CLASS}, .contxtly-btn, .contxtly-tooltip`;

const getUrl = () => new URL(location.href).origin + new URL(location.href).pathname;

// Storage
async function getHighlights() {
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  return highlights[getUrl()] || [];
}

async function saveHighlight(originalText, translation, context) {
  const url = getUrl();
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  if (!highlights[url]) highlights[url] = [];
  // Store both original text (for DOM matching) and lemma (base form for learning)
  const lemma = translation?.lemma || originalText;
  highlights[url].push({ text: originalText, lemma, translation, context, timestamp: Date.now() });
  await chrome.storage.local.set({ highlights });
}

export async function removeFromStorage(lemma) {
  const url = getUrl();
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  if (!highlights[url]) return;
  // Filter by lemma (base form) - this removes all inflected forms of the same word
  highlights[url] = highlights[url].filter((h) => (h.lemma || h.text) !== lemma);
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

// Remove all highlights for a given lemma (checks dataset for matching lemma)
export function removeHighlightFromDOM(lemma) {
  document.querySelectorAll('.contxtly-highlight').forEach((mark) => {
    // Check if this mark's translation has the same lemma
    let data = mark.dataset.translation;
    try { data = JSON.parse(data); } catch {}
    const markLemma = data?.lemma || mark.textContent;
    if (markLemma === lemma) unwrap(mark);
  });
}

// Create delete handler for a highlighted word (uses lemma for deletion)
function createDeleteHandler(lemma) {
  return async () => {
    await removeFromStorage(lemma);
    removeHighlightFromDOM(lemma);
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
    // Use lemma for delete handler
    const lemma = data?.lemma || text || mark.textContent;
    showTranslationTooltip(rect.left, rect.bottom, data, createDeleteHandler(lemma));
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

// Find and highlight a related word in the same block using character offset
function highlightRelatedWord(block, relatedWord, translation, context) {
  if (!block || !relatedWord) return;

  const relatedText = relatedWord.text || relatedWord;
  const offset = relatedWord.offset;

  // If we have an offset and context, use it to find the exact position
  if (offset != null && context) {
    const blockText = block.textContent;
    const ctxStart = blockText.indexOf(context);
    if (ctxStart !== -1) {
      const targetPos = ctxStart + offset; // absolute position in block text

      // Walk ALL text nodes (including inside highlights) to keep char positions aligned
      const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);

      let charCount = 0;
      while (walker.nextNode()) {
        const node = walker.currentNode;
        const nodeLen = node.textContent.length;
        if (charCount + nodeLen > targetPos) {
          // Skip if this node is already inside a highlight
          if (node.parentElement.closest(SKIP)) {
            charCount += nodeLen;
            continue;
          }
          const localIdx = targetPos - charCount;
          try {
            const range = document.createRange();
            range.setStart(node, localIdx);
            range.setEnd(node, localIdx + relatedText.length);
            range.surroundContents(createMark(translation, relatedText));
            return;
          } catch { /* surroundContents throws on cross-element boundaries */ }
        }
        charCount += nodeLen;
      }
    }
  }

  // Fallback: simple text search (for legacy data without offsets)
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT :
                       n.textContent.includes(relatedText) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
  });

  while (walker.nextNode()) {
    const node = walker.currentNode;
    const idx = node.textContent.indexOf(relatedText);
    if (idx === -1) continue;

    try {
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + relatedText.length);
      range.surroundContents(createMark(translation, relatedText));
      return;
    } catch { /* surroundContents throws on cross-element boundaries */ }
  }
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
  const block = parent?.closest("p, div, li, td, article, section") || document.body;

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

  // Highlight related words (other parts of separable verb or collocation)
  const ctxSentence = translation?.context_translation?.source || "";
  for (const word of translation?.related_words || []) {
    highlightRelatedWord(block, word, translation, ctxSentence);
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
    // Remove highlights by lemma
    const targetLemma = msg.lemma || msg.text;
    document.querySelectorAll(`.${CLASS}`).forEach((mark) => {
      let data = mark.dataset.translation;
      try { data = JSON.parse(data); } catch {}
      const markLemma = data?.lemma || mark.textContent;
      if (markLemma === targetLemma) unwrap(mark);
    });
  }
});

// Close tooltip on outside click
document.addEventListener("click", (e) => {
  if (!e.target.closest(`.${CLASS}`) && !e.target.closest(".contxtly-tooltip")) {
    removeTooltip();
  }
});

restore();

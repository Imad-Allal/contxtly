const HIGHLIGHT_CLASS = "contxtly-highlight";
const SKIP_SELECTOR = `.${HIGHLIGHT_CLASS}, .contxtly-btn, .contxtly-tooltip`;

const getPageUrl = () => {
  const u = new URL(window.location.href);
  return u.origin + u.pathname;
};

// Storage
async function getPageHighlights() {
  const { highlights = {} } = await chrome.storage.local.get("highlights");
  return highlights[getPageUrl()] || [];
}

async function saveToStorage(text, translation, context) {
  const url = getPageUrl();
  const { highlights = {} } = await chrome.storage.local.get("highlights");

  if (!highlights[url]) highlights[url] = [];
  highlights[url].push({ text, translation, context });
  await chrome.storage.local.set({ highlights });
}

// Check cache
export async function getCachedTranslation(text) {
  const found = (await getPageHighlights()).find((h) => h.text === text);
  return found?.translation || null;
}

// Unwrap a mark element, keeping its children
function unwrap(el) {
  const parent = el.parentNode;
  while (el.firstChild) parent.insertBefore(el.firstChild, el);
  parent.removeChild(el);
  parent.normalize();
}

// Create mark element
function createMark(translation) {
  const mark = document.createElement("mark");
  mark.className = HIGHLIGHT_CLASS;
  mark.dataset.translation = translation;
  return mark;
}

// Get surrounding context to uniquely identify a text occurrence
function getContext(range, text) {
  const container = range.commonAncestorContainer;
  const block = container.nodeType === Node.TEXT_NODE ? container.parentElement : container;
  const parent = block?.closest("p, div, li, td, article, section") || block;
  const fullText = parent?.textContent || "";
  const idx = fullText.indexOf(text);
  if (idx === -1) return "";
  // Get ~30 chars before and after
  const start = Math.max(0, idx - 30);
  const end = Math.min(fullText.length, idx + text.length + 30);
  return fullText.slice(start, end);
}

// Highlight the selected range
export async function highlightSelection(range, text, translation) {
  if (!range) return;

  // Skip if selection is inside an existing highlight with same text
  const container = range.commonAncestorContainer;
  const parentEl = container.nodeType === Node.TEXT_NODE ? container.parentElement : container;
  const existingMark = parentEl?.closest?.(`.${HIGHLIGHT_CLASS}`);
  if (existingMark && existingMark.textContent === text) {
    return;
  }

  // If selection overlaps existing highlights, unwrap them first
  if (existingMark || parentEl?.querySelector?.(`.${HIGHLIGHT_CLASS}`)) {
    const root = parentEl?.closest("p, div, li, td, article, section") || document.body;
    const marks = [...root.querySelectorAll(`.${HIGHLIGHT_CLASS}`)];

    for (const mark of marks) {
      try {
        const markRange = document.createRange();
        markRange.selectNode(mark);
        const overlaps =
          range.compareBoundaryPoints(Range.END_TO_START, markRange) <= 0 &&
          range.compareBoundaryPoints(Range.START_TO_END, markRange) >= 0;
        if (overlaps) unwrap(mark);
      } catch {}
    }
  }

  // Get context before wrapping (DOM will change after)
  const context = getContext(range, text);

  // Now wrap the selection
  try {
    const mark = createMark(translation);
    range.surroundContents(mark);
  } catch {
    // Cross-element selection - extract, flatten, wrap
    try {
      const contents = range.extractContents();
      contents.querySelectorAll?.(`.${HIGHLIGHT_CLASS}`).forEach(unwrap);
      const mark = createMark(translation);
      mark.appendChild(contents);
      range.insertNode(mark);
    } catch {}
  }

  await saveToStorage(text, translation, context);
}

// Find and highlight specific occurrence using context
function highlightText(text, translation, context) {
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: (node) => {
      if (node.parentElement.closest(SKIP_SELECTOR)) return NodeFilter.FILTER_REJECT;
      return node.textContent.includes(text) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    },
  });

  while (walker.nextNode()) {
    const node = walker.currentNode;
    const idx = node.textContent.indexOf(text);
    if (idx === -1) continue;

    // Check if this occurrence matches the stored context
    const block = node.parentElement?.closest("p, div, li, td, article, section") || node.parentElement;
    const blockText = block?.textContent || "";

    // If context provided, only highlight if context matches
    if (context && !blockText.includes(context.slice(10, -10))) continue;

    const range = document.createRange();
    range.setStart(node, idx);
    range.setEnd(node, idx + text.length);

    try {
      range.surroundContents(createMark(translation));
      return; // Only highlight first matching occurrence
    } catch {}
  }
}

// Restore highlights on page load
async function restoreHighlights() {
  const highlights = await getPageHighlights();
  for (const { text, translation, context } of highlights) {
    highlightText(text, translation, context || "");
  }
}

restoreHighlights();

import { showButton, removeButton, showTooltip, updateTooltip, removeTooltip, isOwnElement } from "./ui.js";
import { highlightSelection, getCachedTranslation, removeFromStorage, removeHighlightFromDOM } from "./highlight.js";

const MAX_LENGTH = 500;
const LETTER_OR_NUM = /\p{L}|\p{N}/u;

// Common abbreviations that don't end sentences (lowercase for matching)
const ABBREVIATIONS = new Set([
  "dr", "mr", "mrs", "ms", "prof", "sr", "jr", "st", "ave", "blvd",
  "dept", "est", "vol", "vs", "etc", "inc", "ltd", "co", "corp",
  "gen", "gov", "sgt", "cpl", "pvt", "capt", "lt", "col", "maj",
  "rev", "hon", "pres", "govt",
  // German
  "bzw", "usw", "evtl", "ggf", "ca", "nr", "tel", "str", "z.b",
]);

/**
 * Determines if a period at position `i` in `text` is a true sentence-ending period.
 * Returns false for abbreviations, decimals, URLs, ellipses, etc.
 */
function isSentenceEnd(text, i) {
  const ch = text[i];

  // ! and ? are always sentence-enders
  if (ch === "!" || ch === "?") return true;
  if (ch !== ".") return false;

  // Must be followed by whitespace/end to even consider it a sentence boundary
  if (i + 1 < text.length && !/\s/.test(text[i + 1])) return false;

  // Ellipsis: "..."
  if ((i >= 1 && text[i - 1] === ".") || (i + 1 < text.length && text[i + 1] === ".")) return false;

  // Decimal number: digit before and digit after the dot (already caught by no-space check above,
  // but guard against edge cases like "3. ")
  if (i >= 1 && /\d/.test(text[i - 1])) {
    // Look ahead past the space — if next non-space is a digit, likely a decimal split by formatting
    // But "3. The answer" is a valid sentence end (numbered list), so only reject if next word is a digit
    const afterSpace = text.slice(i + 1).match(/^\s*(\S)/);
    if (afterSpace && /\d/.test(afterSpace[1])) return false;
  }

  // Abbreviation check: grab the word immediately before the period
  let wordStart = i - 1;
  while (wordStart >= 0 && /\p{L}/u.test(text[wordStart])) wordStart--;
  wordStart++;
  const wordBefore = text.slice(wordStart, i).toLowerCase();

  if (wordBefore.length > 0) {
    // Single-letter abbreviation (e.g. "A.", "B.", initials) — not a sentence end
    // unless the next word starts lowercase (which would be unusual after an initial)
    if (wordBefore.length === 1) {
      const nextWord = text.slice(i + 1).match(/^\s+(\p{L})/u);
      if (!nextWord || /\p{Lu}/u.test(nextWord[1])) return false;
    }

    if (ABBREVIATIONS.has(wordBefore)) return false;
  }

  return true;
}

// Trim selection to letters/numbers only
function trimRange(selection) {
  if (!selection.rangeCount) return null;

  const range = selection.getRangeAt(0).cloneRange();
  const text = selection.toString();

  let start = 0, end = text.length;
  for (let i = 0; i < text.length; i++) if (LETTER_OR_NUM.test(text[i])) { start = i; break; }
  for (let i = text.length - 1; i >= 0; i--) if (LETTER_OR_NUM.test(text[i])) { end = i + 1; break; }

  if (start > 0) range.setStart(range.startContainer, range.startOffset + start);
  if (end < text.length) range.setEnd(range.endContainer, range.endOffset - (text.length - end));

  return range;
}

// Extract sentence context
function extractSentence(selection) {
  if (!selection.rangeCount) return null;

  const range = selection.getRangeAt(0);
  const block = getBlock(range.commonAncestorContainer);
  if (!block) return null;

  const fullText = block.textContent || "";
  const selected = selection.toString().trim();
  const start = getOffset(block, range.startContainer, range.startOffset);
  if (start === -1) return null;

  const sentStart = findBoundary(fullText, start, -1);
  const sentEnd = findBoundary(fullText, start + selected.length, 1);
  const sentence = fullText.slice(sentStart, sentEnd).trim();

  return sentence !== selected ? sentence : null;
}

function getBlock(node) {
  const tags = ["P", "DIV", "LI", "TD", "TH", "BLOCKQUOTE", "H1", "H2", "H3", "H4", "H5", "H6", "ARTICLE", "SECTION"];
  let el = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;

  while (el && el !== document.body) {
    if (tags.includes(el.tagName)) return el;
    el = el.parentElement;
  }

  return node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
}

function getOffset(block, container, offset) {
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
  let pos = 0;

  while (walker.nextNode()) {
    if (walker.currentNode === container) return pos + offset;
    pos += walker.currentNode.textContent.length;
  }

  return -1;
}

function findBoundary(text, pos, dir) {
  const step = dir < 0 ? -1 : 1;
  const start = dir < 0 ? pos - 1 : pos;

  for (let i = start; dir < 0 ? i >= 0 : i < text.length; i += step) {
    if (isSentenceEnd(text, i)) {
      if (dir < 0 && i + 1 < text.length && /\s/.test(text[i + 1])) return i + 2;
      if (dir > 0) return i + 1;
    }
  }

  return dir < 0 ? 0 : text.length;
}

// Create delete handler for a translation
function createDeleteHandler(text) {
  return async () => {
    await removeFromStorage(text);
    removeHighlightFromDOM(text);
  };
}

// Translate
async function translate(text, context, range, x, y) {
  showTooltip(x, y);

  try {
    const cached = await getCachedTranslation(text, context);
    if (cached) {
      return updateTooltip(cached, false, createDeleteHandler(text));
    }

    const res = await chrome.runtime.sendMessage({ action: "translate", data: { text, context } });

    if (res.error) {
      updateTooltip(res.error, true);
    } else {
      // Use lemma (base form) for storage key if available
      const wordToSave = res.lemma || text;
      updateTooltip(res, false, createDeleteHandler(wordToSave));
      highlightSelection(range, text, res);
    }
  } catch {
    updateTooltip("Translation failed", true);
  }
}

// Event handlers
function dismissPopups() {
  removeButton();
  removeTooltip();
}

document.addEventListener("mouseup", (e) => {
  if (isOwnElement(e.target)) return;

  const selection = window.getSelection();
  const raw = selection.toString().trim();

  dismissPopups();

  if (raw.length > 0 && raw.length < MAX_LENGTH) {
    const context = extractSentence(selection);
    const range = trimRange(selection);
    const text = range?.toString() || raw;

    const rect = (range || selection.getRangeAt(0)).getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.bottom;

    showButton(x, y, () => translate(text, context, range, x, y));
  }
});

document.addEventListener("mousedown", (e) => !isOwnElement(e.target) && dismissPopups());
document.addEventListener("keydown", (e) => e.key === "Escape" && dismissPopups());

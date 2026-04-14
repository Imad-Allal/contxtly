import { showTranslationTooltip, removeTooltip, getHighlightTypeClass, applyHighlightStyle } from "./ui.js";

const CLASS = "contxtly-highlight";
const SKIP = `.${CLASS}, .contxtly-btn, .contxtly-tooltip`;

// ── Translation cache (in-memory read cache, survives page nav via storage) ───

function cacheKey(text, context) {
  return context ? `${text}|||${context}` : text;
}

export async function getCachedTranslation(text, context) {
  const { translation_cache = {} } = await chrome.storage.local.get("translation_cache");
  return translation_cache[cacheKey(text, context)] || null;
}

async function saveTranslationCache(text, context, translation) {
  const { translation_cache = {} } = await chrome.storage.local.get("translation_cache");
  translation_cache[cacheKey(text, context)] = translation;
  for (const related of translation?.related_words || []) {
    const relatedText = related.text || related;
    if (relatedText) translation_cache[cacheKey(relatedText, context)] = translation;
  }
  await chrome.storage.local.set({ translation_cache });
}

// ── DOM helpers ───────────────────────────────────────────────────────────────

function unwrap(el) {
  const parent = el.parentNode;
  while (el.firstChild) parent.insertBefore(el.firstChild, el);
  parent.removeChild(el);
  parent.normalize();
}

function createMark(translation, text) {
  const mark = document.createElement("mark");
  const typeClass = getHighlightTypeClass(translation);
  mark.className = typeClass ? `${CLASS} ${typeClass}` : CLASS;
  applyHighlightStyle(mark, typeClass);
  mark.dataset.translation = typeof translation === "object" ? JSON.stringify(translation) : translation;

  mark.onclick = (e) => {
    e.stopPropagation();
    const rect = mark.getBoundingClientRect();
    let data = mark.dataset.translation;
    try { data = JSON.parse(data); } catch {}
    const lemma = data?.lemma || text || mark.textContent;
    showTranslationTooltip(rect.left, rect.bottom, data, () => deleteWord(lemma));
  };

  return mark;
}

function getContextAndOffset(range, text) {
  const el = range.commonAncestorContainer;
  const block = (el.nodeType === Node.TEXT_NODE ? el.parentElement : el)?.closest("p, div, li, td, article, section");
  if (!block) return { context: "", offset: null };

  try {
    const preRange = document.createRange();
    preRange.setStart(block, 0);
    preRange.setEnd(range.startContainer, range.startOffset);
    const offset = preRange.toString().length;
    const full = block.textContent;
    const context = full.slice(Math.max(0, offset - 30), Math.min(full.length, offset + text.length + 30));
    console.log(`[contxtly] saved "${text}": offset=${offset}, block tag=${block.tagName}, block len=${full.length}`);
    return { context, offset };
  } catch {
    return { context: "", offset: null };
  }
}

// ── Related word highlighting ─────────────────────────────────────────────────

function highlightRelatedWord(block, relatedWord, translation, context) {
  if (!block || !relatedWord) return;

  const relatedText = relatedWord.text || relatedWord;
  const offset = relatedWord.offset;

  if (offset != null && context) {
    const blockText = block.textContent;
    const ctxStart = blockText.indexOf(context);
    if (ctxStart !== -1) {
      const targetPos = ctxStart + offset;
      const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
      let charCount = 0;
      while (walker.nextNode()) {
        const node = walker.currentNode;
        const nodeLen = node.textContent.length;
        if (charCount + nodeLen > targetPos) {
          if (node.parentElement.closest(SKIP)) { charCount += nodeLen; continue; }
          const localIdx = targetPos - charCount;
          try {
            const range = document.createRange();
            range.setStart(node, localIdx);
            range.setEnd(node, localIdx + relatedText.length);
            range.surroundContents(createMark(translation, relatedText));
            return;
          } catch {}
        }
        charCount += nodeLen;
      }
    }
  }

  // Fallback: simple text search
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
    } catch {}
  }
}

// ── Core DOM apply (no storage) ───────────────────────────────────────────────

export function applyHighlightToDOM(range, text, translation) {
  if (!range) return;

  const container = range.commonAncestorContainer;
  const parent = container.nodeType === Node.TEXT_NODE ? container.parentElement : container;
  const existing = parent?.closest?.(`.${CLASS}`);

  if (existing?.textContent === text) return;

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

  const ctxSentence = translation?.context_translation?.source || "";
  for (const word of translation?.related_words || []) {
    highlightRelatedWord(block, word, translation, ctxSentence);
  }
}

// ── Unified save ──────────────────────────────────────────────────────────────

/**
 * Full save flow:
 * 1. Apply highlight to DOM
 * 2. Save to wordStore (instant)
 * 3. Cache translation
 * 4. Fire DB save async → patch dbId → check for race (deleted before DB responded)
 */
export async function highlightSelection(range, text, translation) {
  if (!range) return;

  applyHighlightToDOM(range, text, translation);
  const { context, offset } = getContextAndOffset(range, text);
  await saveTranslationCache(text, context, translation);
  const lemma = translation?.lemma || text;

  // Compute offsets for all cluster members so each part can be precisely restored
  const el = range.commonAncestorContainer;
  const block = (el.nodeType === Node.TEXT_NODE ? el.parentElement : el)?.closest("p, div, li, td, article, section");
  const blockText = block?.textContent || "";
  const ctxSentence = translation?.context_translation?.source || "";
  const ctxStart = ctxSentence ? blockText.indexOf(ctxSentence) : -1;

  const clusterMembers = [{ text, offset }];
  for (const related of translation?.related_words || []) {
    const relatedText = related.text || related;
    let relatedOffset = null;
    if (related.offset != null && ctxStart !== -1) {
      relatedOffset = ctxStart + related.offset;
    } else if (relatedText) {
      const idx = blockText.indexOf(relatedText);
      if (idx !== -1) relatedOffset = idx;
    }
    clusterMembers.push({ text: relatedText, offset: relatedOffset });
  }

  const res = await chrome.runtime.sendMessage({
    action: "wsSaveWord",
    data: { text, lemma, translation, context, offset, source_url: location.href, clusterMembers },
  });

  if (!res?.duplicate) {
    chrome.runtime.sendMessage({
      action: "dbSaveWord",
      data: { localId: res?.localId ?? res, text, lemma, translation, context, offset, source_url: location.href, clusterMembers },
    }).catch(() => {});
  }
}

// ── Unified delete ────────────────────────────────────────────────────────────

/**
 * Full delete flow:
 * 1. Remove highlight from DOM (this tab)
 * 2. Archive in wordStore
 * 3. Broadcast DOM removal to all other tabs
 * 4. Fire DB soft-delete async (background handles auto-purge if archives overflow)
 */
export async function deleteWord(lemma) {
  removeHighlightFromDOM(lemma);

  await chrome.runtime.sendMessage({
    action: "wsArchiveWord",
    data: { lemma },
  });
}

export function removeHighlightFromDOM(lemma) {
  document.querySelectorAll(".contxtly-highlight").forEach((mark) => {
    let data = mark.dataset.translation;
    try { data = JSON.parse(data); } catch {}
    const markLemma = data?.lemma || mark.textContent;
    if (markLemma === lemma) unwrap(mark);
  });
}

export function removeClusterFromDOM(clusterMembers) {
  const texts = new Set((clusterMembers || []).map((m) => m.text).filter(Boolean));
  document.querySelectorAll(".contxtly-highlight").forEach((mark) => {
    if (texts.has(mark.textContent)) unwrap(mark);
  });
}

// ── Restore (single word, from message) ──────────────────────────────────────

function restoreHighlightToDOM(text, translation, context, offset) {
  const block = offset != null ? findBlockByOffset(text, offset) : null;

  if (block) {
    const restored = restoreByOffset(block, text, translation, offset);
    if (restored) {
      console.log(`[contxtly] restored "${text}" via offset`);
      const ctxSentence = translation?.context_translation?.source || "";
      for (const word of translation?.related_words || []) {
        highlightRelatedWord(block, word, translation, ctxSentence);
      }
      return;
    }
    console.log(`[contxtly] offset mismatch for "${text}", falling back to context`);
  }

  // Context fallback
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT :
                       n.textContent.includes(text) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT,
  });

  while (walker.nextNode()) {
    const node = walker.currentNode;
    const idx = node.textContent.indexOf(text);
    if (idx === -1) continue;
    const block = node.parentElement?.closest("p, div, li, td, article, section");
    const contextSnippet = context?.slice(10, -10);
    if (contextSnippet && !block?.textContent?.includes(contextSnippet)) continue;
    try {
      const range = document.createRange();
      range.setStart(node, idx);
      range.setEnd(node, idx + text.length);
      range.surroundContents(createMark(translation, text));
      console.log(`[contxtly] restored "${text}" via context`);
      if (block) {
        const ctxSentence = translation?.context_translation?.source || "";
        for (const word of translation?.related_words || []) {
          highlightRelatedWord(block, word, translation, ctxSentence);
        }
      }
      return;
    } catch {}
  }
}

// ── Offset-based restore helpers ──────────────────────────────────────────────

function findBlockByOffset(text, offset) {
  // Find the most specific (deepest) block where text sits at the exact offset
  // querySelectorAll returns in document order — later matches are deeper in the tree
  const blocks = document.querySelectorAll("p, li, td, article, section, div");
  let best = null;
  for (const block of blocks) {
    if (block.textContent.slice(offset, offset + text.length) === text) {
      best = block; // keep overwriting — last match is deepest
    }
  }
  return best;
}

function restoreByOffset(block, text, translation, offset) {
  let charCount = 0;
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode;
    const nodeLen = node.textContent.length;
    if (charCount + nodeLen > offset) {
      if (node.parentElement.closest(SKIP)) {
        // Already highlighted — check if the mark covers exactly the right text at this offset
        const mark = node.parentElement.closest(`.${CLASS}`);
        if (mark && mark.textContent === text) {
          console.log(`[contxtly] "${text}" already highlighted at offset ${offset}, skipping re-wrap`);
          return true;
        }
        charCount += nodeLen;
        continue;
      }
      const localIdx = offset - charCount;
      if (node.textContent.slice(localIdx, localIdx + text.length) !== text) return false;
      try {
        const range = document.createRange();
        range.setStart(node, localIdx);
        range.setEnd(node, localIdx + text.length);
        range.surroundContents(createMark(translation, text));
        return true;
      } catch { return false; }
    }
    charCount += nodeLen;
  }
  return false;
}

// ── Page restore (on load) ────────────────────────────────────────────────────

async function restore() {
  const { words = [] } = await chrome.storage.local.get("words");
  if (!words.length) return;

  const pending = words.map((h) => ({ ...h, done: false }));

  // Pre-pass: any word already in the DOM as a highlight can be skipped immediately
  for (const h of pending) {
    if (h.done) continue;
    for (const mark of document.querySelectorAll(`.${CLASS}`)) {
      let data = mark.dataset.translation;
      try { data = JSON.parse(data); } catch {}
      const markLemma = data?.lemma || mark.textContent;
      if (markLemma === (h.lemma || h.text) || mark.textContent === h.text) {
        console.log(`[contxtly] "${h.text}" already in DOM, skipping restore`);
        h.done = true;
        break;
      }
    }
  }

  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => n.parentElement.closest(SKIP) ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
  });

  while (walker.nextNode()) {
    if (pending.every((h) => h.done)) break;

    const node = walker.currentNode;
    const nodeText = node.textContent;
    const block = node.parentElement?.closest("p, div, li, td, article, section");

    for (const h of pending) {
      if (h.done) continue;
      if (!nodeText.includes(h.text)) continue;

      const idx = nodeText.indexOf(h.text);

      // Offset-first — find the exact block the offset belongs to, independent of current walker node
      if (h.offset != null) {
        const offsetBlock = findBlockByOffset(h.text, h.offset);
        console.log(`[contxtly] offset restore "${h.text}": offset=${h.offset}, block found=${!!offsetBlock}, block tag=${offsetBlock?.tagName}, block text preview="${offsetBlock?.textContent?.slice(0, 60)}"`);
        if (offsetBlock) {
          const restored = restoreByOffset(offsetBlock, h.text, h.translation, h.offset);
          if (restored) {
            console.log(`[contxtly] restored "${h.text}" via offset`);
            h.done = true;
            const ctxSentence = h.translation?.context_translation?.source || "";
            for (const word of h.translation?.related_words || []) {
              highlightRelatedWord(offsetBlock, word, h.translation, ctxSentence);
            }
            continue;
          }
          console.log(`[contxtly] restoreByOffset failed for "${h.text}" at offset=${h.offset} in block "${offsetBlock?.textContent?.slice(0, 60)}"`);
        }
        console.log(`[contxtly] offset mismatch for "${h.text}", falling back to context`);
      }

      // Context fallback
      const contextSnippet = h.context?.slice(10, -10);
      if (contextSnippet && !block?.textContent?.includes(contextSnippet)) continue;

      try {
        const range = document.createRange();
        range.setStart(node, idx);
        range.setEnd(node, idx + h.text.length);
        range.surroundContents(createMark(h.translation, h.text));
        console.log(`[contxtly] restored "${h.text}" via context`);
        h.done = true;
        if (block) {
          const ctxSentence = h.translation?.context_translation?.source || "";
          for (const word of h.translation?.related_words || []) {
            highlightRelatedWord(block, word, h.translation, ctxSentence);
          }
        }
      } catch {}
    }
  }
}

// ── Message listener ──────────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((msg) => {
  if (msg.action === "removeHighlight") {
    removeHighlightFromDOM(msg.lemma || msg.text);
  }

  if (msg.action === "removeCluster") {
    removeClusterFromDOM(msg.clusterMembers);
  }

  if (msg.action === "addHighlight") {
    const { text, translation, context, offset } = msg;
    restoreHighlightToDOM(text, translation, context || "", offset ?? null);
  }
});

// Close tooltip on outside click
document.addEventListener("click", (e) => {
  if (!e.target.closest(`.${CLASS}`) && !e.target.closest(".contxtly-tooltip")) {
    removeTooltip();
  }
});

restore();

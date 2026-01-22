import {
  showButton,
  removeButton,
  showTooltip,
  updateTooltip,
  removeTooltip,
  isOwnElement,
} from "./ui.js";

const MAX_TEXT_LENGTH = 500;
const SENTENCE_ENDINGS = /[.!?]/;

document.addEventListener("mouseup", (e) => {
  if (isOwnElement(e.target)) return;

  const selection = window.getSelection();
  const text = selection.toString().trim();

  removeButton();
  removeTooltip();

  if (text.length > 0 && text.length < MAX_TEXT_LENGTH) {
    const context = extractSentence(selection);
    console.log("Extracted context:", context);
    showButton(e.pageX, e.pageY, () => translate(text, context, e.pageX, e.pageY));
  }
});

function extractSentence(selection) {
  if (!selection.rangeCount) return null;

  const range = selection.getRangeAt(0);
  const container = range.commonAncestorContainer;

  // Get the block-level parent element
  const block = getBlockParent(container);
  if (!block) return null;

  const fullText = block.textContent || "";
  const selectedText = selection.toString().trim();

  // Find where the selection starts in the block text
  const selectionStart = findSelectionOffset(block, range.startContainer, range.startOffset);
  if (selectionStart === -1) return null;

  // Find sentence boundaries
  const sentenceStart = findSentenceStart(fullText, selectionStart);
  const sentenceEnd = findSentenceEnd(fullText, selectionStart + selectedText.length);

  const sentence = fullText.slice(sentenceStart, sentenceEnd).trim();

  // Don't return context if it's the same as selected text
  if (sentence === selectedText) return null;

  return sentence;
}

function getBlockParent(node) {
  const blockTags = ["P", "DIV", "LI", "TD", "TH", "BLOCKQUOTE", "H1", "H2", "H3", "H4", "H5", "H6", "ARTICLE", "SECTION"];
  let current = node.nodeType === Node.TEXT_NODE ? node.parentElement : node;

  while (current && current !== document.body) {
    if (blockTags.includes(current.tagName)) {
      return current;
    }
    current = current.parentElement;
  }

  // Fallback: return the immediate parent if no block found
  return node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
}

function findSelectionOffset(block, startContainer, startOffset) {
  const walker = document.createTreeWalker(block, NodeFilter.SHOW_TEXT, null, false);
  let offset = 0;

  while (walker.nextNode()) {
    if (walker.currentNode === startContainer) {
      return offset + startOffset;
    }
    offset += walker.currentNode.textContent.length;
  }

  return -1;
}

function findSentenceStart(text, position) {
  // Walk backwards to find sentence start
  for (let i = position - 1; i >= 0; i--) {
    if (SENTENCE_ENDINGS.test(text[i])) {
      // Check if followed by space (to avoid matching abbreviations mid-word)
      if (i + 1 < text.length && /\s/.test(text[i + 1])) {
        return i + 2; // Start after the punctuation and space
      }
    }
  }
  return 0; // Beginning of text
}

function findSentenceEnd(text, position) {
  // Walk forwards to find sentence end
  for (let i = position; i < text.length; i++) {
    if (SENTENCE_ENDINGS.test(text[i])) {
      return i + 1; // Include the punctuation
    }
  }
  return text.length; // End of text
}

document.addEventListener("mousedown", (e) => {
  if (!isOwnElement(e.target)) {
    removeButton();
    removeTooltip();
  }
});

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    removeButton();
    removeTooltip();
  }
});

async function translate(text, context, x, y) {
  showTooltip(x, y);

  try {
    const response = await chrome.runtime.sendMessage({
      action: "translate",
      data: { text, context },
    });

    if (response.error) {
      updateTooltip(response.error, true);
    } else {
      updateTooltip(response.translation);
    }
  } catch (err) {
    updateTooltip("Translation failed", true);
  }
}

import {
  showButton,
  removeButton,
  showTooltip,
  updateTooltip,
  removeTooltip,
  isOwnElement,
} from "./ui.js";
import { CONFIG } from "../config.js";

document.addEventListener("mouseup", (e) => {
  if (isOwnElement(e.target)) return;

  const selection = window.getSelection();
  const text = selection.toString().trim();

  removeButton();
  removeTooltip();

  if (text.length > 0 && text.length < CONFIG.MAX_TEXT_LENGTH) {
    showButton(e.pageX, e.pageY, () => translate(text, e.pageX, e.pageY));
  }
});

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

async function translate(text, x, y) {
  showTooltip(x, y);

  try {
    const response = await chrome.runtime.sendMessage({
      action: "translate",
      data: { text },
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

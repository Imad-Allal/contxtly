import { CONFIG } from "../config.js";
const API_URL = CONFIG.apiUrl;

const DEFAULT_SETTINGS = {
  targetLang: CONFIG.DEFAULT_TARGET_LANG,
  mode: CONFIG.DEFAULT_MODE,
};

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(["settings"], (result) => {
    if (!result.settings) {
      chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
    }
  });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "translate") {
    handleTranslate(request.data)
      .then(sendResponse)
      .catch((err) => sendResponse({ error: err.message }));
    return true;
  }

  if (request.action === "getSettings") {
    chrome.storage.local.get(["settings"], (result) => {
      sendResponse(result.settings || DEFAULT_SETTINGS);
    });
    return true;
  }

  if (request.action === "saveSettings") {
    chrome.storage.local.set({ settings: request.data }, () => {
      sendResponse({ success: true });
    });
    return true;
  }
});

async function handleTranslate({ text, context }) {
  const { settings } = await chrome.storage.local.get(["settings"]);
  const { targetLang, mode } = settings || DEFAULT_SETTINGS;

  const res = await fetch(`${API_URL}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      target_lang: targetLang,
      mode,
      context: context || null,
    }),
  });

  if (!res.ok) {
    const error = await res.text();
    throw new Error(error || "API error");
  }

  return res.json();
}

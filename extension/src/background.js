import { handleExportToAnki } from "./anki.js";
import { getAccessToken, login, logout } from "./auth.js";

const API_URL = import.meta.env.VITE_API_URL;

const DEFAULT_SETTINGS = {
  targetLang: "en",
  mode: "smart",
};

// ── Helpers ───────────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const token = await getAccessToken();
  if (!token) throw new Error("NOT_AUTHENTICATED");

  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`,
      ...(options.headers || {}),
    },
  });

  if (res.status === 401) throw new Error("NOT_AUTHENTICATED");
  if (res.status === 429) {
    const body = await res.json();
    throw new Error(JSON.stringify({ code: "LIMIT_REACHED", ...body.detail }));
  }
  if (!res.ok) throw new Error((await res.text()) || "API error");

  if (res.status === 204) return null;
  return res.json();
}

// ── Message handlers ──────────────────────────────────────────────────────────

async function handleTranslate({ text, context, text_offset }) {
  const { settings } = await chrome.storage.local.get(["settings"]);
  const { targetLang, mode } = settings || DEFAULT_SETTINGS;

  return apiFetch("/translate", {
    method: "POST",
    body: JSON.stringify({ text, target_lang: targetLang, mode, context: context || null, text_offset: text_offset ?? null }),
  });
}

async function handleGetUsage() {
  return apiFetch("/usage");
}

async function handleSaveWord(data) {
  return apiFetch("/words", { method: "POST", body: JSON.stringify(data) });
}

async function handleDeleteWord({ id }) {
  return apiFetch(`/words/${id}`, { method: "DELETE" });
}

async function handleGetWords() {
  return apiFetch("/words");
}

async function handleGetCheckoutUrl() {
  return apiFetch("/checkout");
}

async function handleGetPortalUrl() {
  return apiFetch("/portal");
}

// ── Event listeners ───────────────────────────────────────────────────────────

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get(["settings"], (result) => {
    if (!result.settings) chrome.storage.local.set({ settings: DEFAULT_SETTINGS });
  });
});

chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
  const handlers = {
    translate:      () => handleTranslate(request.data),
    getUsage:       () => handleGetUsage(),
    saveWord:       () => handleSaveWord(request.data),
    deleteWord:     () => handleDeleteWord(request.data),
    getWords:       () => handleGetWords(),
    getCheckoutUrl: () => handleGetCheckoutUrl(),
    getPortalUrl:   () => handleGetPortalUrl(),
    login:          () => login(),
    logout:         () => logout().then(() => ({ success: true })),
    getSettings: () =>
      chrome.storage.local.get(["settings"]).then((r) => r.settings || DEFAULT_SETTINGS),
    saveSettings: () =>
      chrome.storage.local.set({ settings: request.data }).then(() => ({ success: true })),
    exportToAnki: () => handleExportToAnki(),
    openUrl: () => {
      chrome.tabs.create({ url: request.data?.url });
      return Promise.resolve({ success: true });
    },
  };

  const handler = handlers[request.action];
  if (!handler) return false;

  handler().then(sendResponse).catch((err) => sendResponse({ error: err.message }));
  return true;
});

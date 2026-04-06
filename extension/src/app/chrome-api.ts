import type { Word } from "./types";

export const isChromeExt =
  typeof chrome !== "undefined" && !!chrome?.runtime?.id;

export async function loadWords(): Promise<Word[]> {
  if (!isChromeExt) return [];

  const { highlights = {} } = await chrome.storage.local.get("highlights");
  const seen = new Set<string>();

  return Object.entries(highlights as Record<string, Word[]>)
    .flatMap(([url, items]) => items.map((h) => ({ ...h, url })))
    .sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0))
    .filter((h) => {
      const key = h.lemma || h.text;
      return !seen.has(key) && seen.add(key);
    });
}

export async function loadSettings(): Promise<{ targetLang: string; mode: string }> {
  if (!isChromeExt) return { targetLang: "en", mode: "smart" };
  return chrome.runtime.sendMessage({ action: "getSettings" });
}

export function saveSettings(data: { targetLang: string; mode: string }) {
  if (!isChromeExt) return;
  chrome.runtime.sendMessage({ action: "saveSettings", data });
}

export async function deleteWords(lemmas: string[]) {
  if (!isChromeExt) return;

  const { highlights = {} } = await chrome.storage.local.get("highlights");
  const h = highlights as Record<string, Word[]>;

  for (const url of Object.keys(h)) {
    h[url] = h[url].filter((w) => !lemmas.includes(w.lemma || w.text));
    if (!h[url].length) delete h[url];
  }

  await chrome.storage.local.set({ highlights: h });

  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    if (tab.id) {
      lemmas.forEach((lemma) =>
        chrome.tabs
          .sendMessage(tab.id!, { action: "removeHighlight", lemma })
          .catch(() => {})
      );
    }
  }
}

export function openUrl(url: string) {
  if (isChromeExt) {
    chrome.tabs.create({ url });
  } else {
    window.open(url, "_blank");
  }
}

export async function getAuthSession(): Promise<{ access_token: string } | null> {
  if (!isChromeExt) return null;
  const { auth } = await chrome.storage.local.get("auth") as { auth?: { access_token: string } };
  return auth || null;
}

export async function login(): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "login" });
}

export async function logout(): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "logout" });
}

export async function getUsage(): Promise<{ used: number; limit: number; plan: string } | null> {
  if (!isChromeExt) return null;
  const res = await chrome.runtime.sendMessage({ action: "getUsage" });
  if (res?.error) return null;
  return res;
}

export async function getPortalUrl(): Promise<string | null> {
  if (!isChromeExt) return null;
  const res = await chrome.runtime.sendMessage({ action: "getPortalUrl" });
  if (res?.error) return null;
  return res?.url || null;
}

export async function getCheckoutUrl(): Promise<string | null> {
  if (!isChromeExt) return null;
  const res = await chrome.runtime.sendMessage({ action: "getCheckoutUrl" });
  if (res?.error) return null;
  return res?.url || null;
}

export async function getWordsFromDB(): Promise<Word[]> {
  if (!isChromeExt) return [];
  const res = await chrome.runtime.sendMessage({ action: "getWords" });
  if (!res || res.error) return [];
  // Map DB rows to the Word shape the UI expects
  return res.map((row: { id: string; text: string; translation: string; data?: object; context?: string; source_url?: string }) => ({
    id: row.id,
    text: row.text,
    lemma: row.text,
    translation: row.data || row.translation,
    url: row.source_url,
    timestamp: undefined,
  }));
}

export async function saveWordToDB(word: { text: string; translation: string; context?: string; source_url?: string; data?: object }): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "saveWord", data: word });
}

export async function deleteWordFromDB(id: string): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "deleteWord", data: { id } });
}

export async function exportToAnki(): Promise<{ msg: string; error: boolean }> {
  if (!isChromeExt) {
    await new Promise((r) => setTimeout(r, 900));
    return { msg: "\u2713 4 added (demo mode)", error: false };
  }

  const res = await chrome.runtime.sendMessage({ action: "exportToAnki" });

  if (res.error) {
    return { msg: "Anki not running. Open Anki with AnkiConnect.", error: true };
  }
  if (res.empty) {
    return { msg: "No words to export.", error: false };
  }

  const parts: string[] = [];
  if (res.added) parts.push(`${res.added} added`);
  if (res.duplicates) parts.push(`${res.duplicates} already in Anki`);
  return { msg: `\u2713 ${parts.join(", ")}`, error: false };
}

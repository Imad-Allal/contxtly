import type { Word } from "./types";

export const isChromeExt =
  typeof chrome !== "undefined" && !!chrome?.runtime?.id;

// ── Words (active) ────────────────────────────────────────────────────────────

/** Load active words from wordStore (instant, no DB call). */
export async function loadWords(): Promise<Word[]> {
  if (!isChromeExt) return [];
  const { words = [] } = await chrome.storage.local.get("words") as { words?: Word[] };
  return words;
}

/**
 * On startup: if wordStore is empty, fetch from DB and seed it.
 * Also seeds archives from DB trash.
 * Called once when the panel opens and auth is confirmed.
 */
export async function syncFromDBIfEmpty(): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "syncFromDBIfEmpty" });
}

/**
 * Archive (soft-delete) words by lemma.
 * Removes from wordStore, moves to archives, broadcasts DOM removal,
 * fires DB soft-delete async.
 */
export async function archiveWords(lemmas: string[]): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "archiveWords", data: { lemmas } });
}

// ── Archives ──────────────────────────────────────────────────────────────────

/** Load archived words from wordStore (instant, no DB call). */
export async function loadArchives(): Promise<Word[]> {
  if (!isChromeExt) return [];
  const { archives = [] } = await chrome.storage.local.get("archives") as { archives?: Word[] };
  return archives;
}

/**
 * Restore archived words by lemma.
 * Moves from archives → words in wordStore, broadcasts DOM re-highlight,
 * fires DB restore async.
 */
export async function restoreWords(lemmas: string[]): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "restoreWords", data: { lemmas } });
}

/**
 * Permanently delete words from archives by lemma.
 * Removes from archives in wordStore, fires DB hard-delete async.
 */
export async function purgeWords(lemmas: string[]): Promise<void> {
  if (!isChromeExt) return;
  await chrome.runtime.sendMessage({ action: "purgeWords", data: { lemmas } });
}

// ── Settings ──────────────────────────────────────────────────────────────────

export async function loadSettings(): Promise<{ targetLang: string; mode: string }> {
  if (!isChromeExt) return { targetLang: "en", mode: "smart" };
  return chrome.runtime.sendMessage({ action: "getSettings" });
}

export function saveSettings(data: { targetLang: string; mode: string }) {
  if (!isChromeExt) return;
  chrome.runtime.sendMessage({ action: "saveSettings", data });
}

// ── Auth ──────────────────────────────────────────────────────────────────────

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

// ── Usage / billing ───────────────────────────────────────────────────────────

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

// ── Misc ──────────────────────────────────────────────────────────────────────

export function openUrl(url: string) {
  if (isChromeExt) {
    chrome.tabs.create({ url });
  } else {
    window.open(url, "_blank");
  }
}

export async function exportToAnki(): Promise<{ msg: string; error: boolean }> {
  if (!isChromeExt) {
    await new Promise((r) => setTimeout(r, 900));
    return { msg: "\u2713 4 added (demo mode)", error: false };
  }

  const res = await chrome.runtime.sendMessage({ action: "exportToAnki" });

  if (res.error) return { msg: "Anki not running. Open Anki with AnkiConnect.", error: true };
  if (res.empty) return { msg: "No words to export.", error: false };

  const parts: string[] = [];
  if (res.added) parts.push(`${res.added} added`);
  if (res.duplicates) parts.push(`${res.duplicates} already in Anki`);
  return { msg: `\u2713 ${parts.join(", ")}`, error: false };
}

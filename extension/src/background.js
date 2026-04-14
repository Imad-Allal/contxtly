import { handleExportToAnki } from "./anki.js";
import { getAccessToken, login, logout } from "./auth.js";
import {
  saveWord as wsSaveWord,
  patchDbId,
  archiveWord as wsArchiveWord,
  archiveWordsBatch as wsArchiveWordsBatch,
  restoreWord as wsRestoreWord,
  restoreWordsBatch as wsRestoreWordsBatch,
  purgeWord as wsPurgeWord,
  purgeWordsBatch as wsPurgeWordsBatch,
  findInArchivesByOffset,
  getWords,
  getArchives,
  seedFromDB,
  seedArchivesFromDB,
  broadcastToAllTabs,
} from "./wordStore.js";

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

// ── Translation ───────────────────────────────────────────────────────────────

async function handleTranslate({ text, context, text_offset }) {
  const { settings } = await chrome.storage.local.get(["settings"]);
  const { targetLang, mode } = settings || DEFAULT_SETTINGS;
  return apiFetch("/translate", {
    method: "POST",
    body: JSON.stringify({ text, target_lang: targetLang, mode, context: context || null, text_offset: text_offset ?? null }),
  });
}

// ── wordStore handlers (all sync to local storage instantly) ──────────────────

/**
 * Save word to wordStore. Returns the localId immediately.
 * If the same word (same offset + source_url) exists in archives, restore it instead.
 */
async function handleWsSaveWord(data, senderTabId) {
  const existing = (await getWords()).find(
    (w) => (w.lemma || w.text) === (data.lemma || data.text) && w.context === data.context
  );
  if (existing) return { localId: existing.localId, duplicate: true };

  const archived = await findInArchivesByOffset(data.offset, data.source_url);
  if (archived) {
    const entry = await wsRestoreWord(archived.lemma || archived.text);
    if (entry) {
      // Exclude the sender tab — it already applied the highlight via applyHighlightToDOM
      broadcastToAllTabs({
        action: "addHighlight",
        text: entry.text,
        translation: entry.translation,
        context: entry.context || "",
        offset: entry.offset ?? null,
      }, senderTabId);
      if (entry.dbId) {
        apiFetch(`/trash/${entry.dbId}/restore`, { method: "POST" }).catch(() => {});
      }
      return { localId: entry.localId, duplicate: true };
    }
  }

  const localId = await wsSaveWord(data);
  return localId;
}

/**
 * Fire DB save, then patch localId with real dbId.
 * If the word was deleted before DB responded, hard-delete from DB.
 */
async function handleDbSaveWord({ localId, text, translation, context, offset, source_url, clusterMembers }) {
  try {
    const translationStr = typeof translation === "string" ? translation : (translation?.translation || "");
    const data = typeof translation === "object" ? { ...translation, cluster_members: clusterMembers || null } : null;
    const row = await apiFetch("/words", {
      method: "POST",
      body: JSON.stringify({ text, translation: translationStr, context, offset, source_url, data }),
    });

    const { orphaned, dbId } = await patchDbId(localId, row.id);
    if (orphaned) {
      // Word deleted before DB responded — clean up DB
      await apiFetch(`/words/${dbId}`, { method: "DELETE" }).catch(() => {});
    }
  } catch (err) {
    console.error("[contxtly] DB save failed:", err.message);
  }
}

/**
 * Archive word: move to archives in wordStore, broadcast DOM removal,
 * soft-delete in DB, auto-purge oldest if archives overflow.
 */
async function handleWsArchiveWord({ lemma }) {
  const { dbId, purgedDbId, clusterMembers } = await wsArchiveWord(lemma);

  // Broadcast removal of all cluster members to all tabs
  await broadcastToAllTabs({ action: "removeCluster", clusterMembers });

  // DB soft-delete async
  if (dbId) {
    apiFetch(`/words/${dbId}`, { method: "DELETE" }).catch(() => {});
  }

  // Auto-purge overflow from DB
  if (purgedDbId) {
    apiFetch(`/trash/${purgedDbId}`, { method: "DELETE" }).catch(() => {});
  }
}

/**
 * Restore word: move from archives → words in wordStore, broadcast re-highlight.
 */
async function handleWsRestoreWord({ lemma }) {
  const entry = await wsRestoreWord(lemma);
  if (!entry) return;

  // Broadcast re-highlight to all tabs
  await broadcastToAllTabs({
    action: "addHighlight",
    text: entry.text,
    translation: entry.translation,
    context: entry.context || "",
    offset: entry.offset ?? null,
  });

  // DB restore async
  if (entry.dbId) {
    apiFetch(`/trash/${entry.dbId}/restore`, { method: "POST" }).catch(() => {});
  }
}

/**
 * Restore multiple words by lemma array.
 */
async function handleWsRestoreWords({ lemmas }) {
  const entries = await wsRestoreWordsBatch(lemmas);
  for (const entry of entries) {
    broadcastToAllTabs({
      action: "addHighlight",
      text: entry.text,
      translation: entry.translation,
      context: entry.context || "",
      offset: entry.offset ?? null,
    });
    if (entry.dbId) apiFetch(`/trash/${entry.dbId}/restore`, { method: "POST" }).catch(() => {});
  }
}

/**
 * Archive multiple words by lemma array.
 */
async function handleWsArchiveWords({ lemmas }) {
  const results = await wsArchiveWordsBatch(lemmas);
  const allMembers = results.flatMap((r) => r.clusterMembers);
  await broadcastToAllTabs({ action: "removeCluster", clusterMembers: allMembers });
  for (const { dbId, purgedDbId } of results) {
    if (dbId) apiFetch(`/words/${dbId}`, { method: "DELETE" }).catch(() => {});
    if (purgedDbId) apiFetch(`/trash/${purgedDbId}`, { method: "DELETE" }).catch(() => {});
  }
}

/**
 * Purge word: remove from archives in wordStore + hard-delete from DB.
 */
async function handleWsPurgeWord({ lemma }) {
  const dbId = await wsPurgeWord(lemma);
  if (dbId) {
    apiFetch(`/trash/${dbId}`, { method: "DELETE" }).catch(() => {});
  }
}

/**
 * Purge multiple words by lemma array.
 */
async function handleWsPurgeWords({ lemmas }) {
  const dbIds = await wsPurgeWordsBatch(lemmas);
  for (const dbId of dbIds) {
    if (dbId) apiFetch(`/trash/${dbId}`, { method: "DELETE" }).catch(() => {});
  }
}

/**
 * On startup: if wordStore is empty, fetch from DB and seed.
 * Also seeds archives from DB trash.
 */
async function handleSyncFromDBIfEmpty() {
  const words = await getWords();
  if (words.length === 0) {
    try {
      const dbWords = await apiFetch("/words");
      if (dbWords?.length) {
        await seedFromDB(dbWords);
        const seeded = await getWords();
        for (const entry of seeded) {
          broadcastToAllTabs({
            action: "addHighlight",
            text: entry.text,
            translation: entry.translation,
            context: entry.context || "",
            offset: entry.offset ?? null,
          });
        }
      }
    } catch (err) {
      console.error("[contxtly] DB sync failed:", err.message);
    }
  }

  const archives = await getArchives();
  if (archives.length === 0) {
    try {
      const dbTrash = await apiFetch("/trash");
      if (dbTrash?.length) await seedArchivesFromDB(dbTrash);
    } catch (err) {
      console.error("[contxtly] DB trash sync failed:", err.message);
    }
  }
}

// ── Misc handlers ─────────────────────────────────────────────────────────────

async function handleGetUsage() {
  return apiFetch("/usage");
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

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  const senderTabId = sender?.tab?.id ?? null;
  const handlers = {
    // Translation
    translate:          () => handleTranslate(request.data),

    // wordStore (instant local ops)
    wsSaveWord:         () => handleWsSaveWord(request.data, senderTabId),
    wsArchiveWord:      () => handleWsArchiveWord(request.data),
    wsArchiveWords:     () => handleWsArchiveWords(request.data),
    wsRestoreWord:      () => handleWsRestoreWord(request.data),
    restoreWords:       () => handleWsRestoreWords(request.data),
    wsPurgeWord:        () => handleWsPurgeWord(request.data),
    purgeWords:         () => handleWsPurgeWords(request.data),
    archiveWords:       () => handleWsArchiveWords(request.data),

    // DB async (fire-and-forget, called from content script)
    dbSaveWord:         () => handleDbSaveWord(request.data),

    // Startup sync
    syncFromDBIfEmpty:  () => handleSyncFromDBIfEmpty(),

    // Usage / billing
    getUsage:           () => handleGetUsage(),
    getCheckoutUrl:     () => handleGetCheckoutUrl(),
    getPortalUrl:       () => handleGetPortalUrl(),

    // Auth
    login:              () => login(),
    logout:             () => logout().then(() => ({ success: true })),

    // Settings
    getSettings:        () => chrome.storage.local.get(["settings"]).then((r) => r.settings || DEFAULT_SETTINGS),
    saveSettings:       () => chrome.storage.local.set({ settings: request.data }).then(() => ({ success: true })),

    // Anki
    exportToAnki:       () => handleExportToAnki(),

    // Misc
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

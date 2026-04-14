/**
 * wordStore.js — single source of truth for saved words in browser local storage.
 *
 * Schema:
 *   chrome.storage.local = {
 *     words:    WordEntry[]   // active words
 *     archives: WordEntry[]   // soft-deleted words (max 10)
 *   }
 *
 * WordEntry = {
 *   localId:     string,   // crypto.randomUUID() — stable local key
 *   dbId:        string?,  // set async once DB confirms the save
 *   text:        string,
 *   lemma:       string,
 *   translation: object,
 *   context:     string,
 *   offset:      number?,  // char offset within block for precise restore
 *   source_url:  string,
 *   timestamp:   number,
 * }
 */

const MAX_ARCHIVES = 10;

// ── Raw read/write ────────────────────────────────────────────────────────────

export async function getWords() {
  const { words = [] } = await chrome.storage.local.get("words");
  return words;
}

export async function getArchives() {
  const { archives = [] } = await chrome.storage.local.get("archives");
  return archives;
}

async function setWords(words) {
  await chrome.storage.local.set({ words });
}

async function setArchives(archives) {
  await chrome.storage.local.set({ archives });
}

// ── Save ──────────────────────────────────────────────────────────────────────

/**
 * Add a new word. Returns the localId immediately so the caller can track it.
 * dbId is patched in later via patchDbId() once the DB confirms.
 */
export async function saveWord({ text, lemma, translation, context, offset, source_url, clusterMembers }) {
  const words = await getWords();
  const localId = crypto.randomUUID();
  words.unshift({
    localId,
    dbId: null,
    text,
    lemma: lemma || text,
    translation,
    context,
    offset: offset ?? null,
    source_url,
    clusterMembers: clusterMembers || [{ text, offset: offset ?? null }],
    timestamp: Date.now(),
  });
  await setWords(words);
  return localId;
}

/**
 * Once DB save resolves, attach the real DB id to the entry.
 * If the entry is gone (deleted before DB responded), return the dbId so the
 * caller can immediately fire a DB delete.
 */
export async function patchDbId(localId, dbId) {
  const words = await getWords();
  const entry = words.find((w) => w.localId === localId);
  if (!entry) {
    // Word was deleted before DB responded — signal caller to clean up DB
    return { orphaned: true, dbId };
  }
  entry.dbId = dbId;
  await setWords(words);
  return { orphaned: false };
}

// ── Delete (archive) ──────────────────────────────────────────────────────────

/**
 * Move a word from words → archives by lemma.
 * If archives exceed MAX_ARCHIVES, purge the oldest and return its dbId
 * so the caller can hard-delete it from DB.
 */
export async function archiveWord(lemma) {
  const [result] = await archiveWordsBatch([lemma]);
  return result;
}

export async function archiveWordsBatch(lemmas) {
  const words = await getWords();
  const archives = await getArchives();
  const results = [];

  for (const lemma of lemmas) {
    const idx = words.findIndex((w) => (w.lemma || w.text) === lemma);
    if (idx === -1) { results.push({ dbId: null, purgedDbId: null, clusterMembers: [] }); continue; }
    const [entry] = words.splice(idx, 1);
    archives.unshift(entry);
    let purgedDbId = null;
    if (archives.length > MAX_ARCHIVES) {
      const purged = archives.pop();
      purgedDbId = purged.dbId || null;
    }
    results.push({ dbId: entry.dbId || null, purgedDbId, clusterMembers: entry.clusterMembers || [{ text: entry.text, offset: entry.offset }] });
  }

  await setWords(words);
  await setArchives(archives);
  return results;
}

// ── Restore ───────────────────────────────────────────────────────────────────

/**
 * Find an archived entry by exact offset + source_url match.
 * Returns the entry if found, null otherwise.
 */
export async function findInArchivesByOffset(offset, source_url) {
  if (offset == null) return null;
  const archives = await getArchives();
  return archives.find((w) => {
    if (w.source_url !== source_url) return false;
    if (w.offset === offset) return true;
    return (w.clusterMembers || []).some((m) => m.offset === offset);
  }) || null;
}

/**
 * Move a word from archives → words by lemma.
 * Returns the full entry so the caller can re-highlight and sync DB.
 */
export async function restoreWord(lemma) {
  const [entry] = await restoreWordsBatch([lemma]);
  return entry || null;
}

export async function restoreWordsBatch(lemmas) {
  const archives = await getArchives();
  const words = await getWords();
  const entries = [];

  for (const lemma of lemmas) {
    const idx = archives.findIndex((w) => (w.lemma || w.text) === lemma);
    if (idx === -1) continue;
    const [entry] = archives.splice(idx, 1);
    words.unshift(entry);
    entries.push(entry);
  }

  await setArchives(archives);
  await setWords(words);
  return entries;
}

// ── Purge (hard delete from archives) ────────────────────────────────────────

/**
 * Permanently remove a word from archives by lemma.
 * Returns the dbId so the caller can hard-delete from DB.
 */
export async function purgeWord(lemma) {
  const [dbId] = await purgeWordsBatch([lemma]);
  return dbId;
}

export async function purgeWordsBatch(lemmas) {
  const archives = await getArchives();
  const dbIds = [];
  for (const lemma of lemmas) {
    const idx = archives.findIndex((w) => (w.lemma || w.text) === lemma);
    if (idx === -1) { dbIds.push(null); continue; }
    const [entry] = archives.splice(idx, 1);
    dbIds.push(entry.dbId || null);
  }
  await setArchives(archives);
  return dbIds;
}

// ── Startup sync ──────────────────────────────────────────────────────────────

/**
 * If words store is empty, populate it from DB rows.
 * DB rows shape: { id, text, translation, context, offset, source_url, data }
 */
function rowToEntry(row) {
  const translation = row.data || row.translation;
  const clusterMembers = row.data?.cluster_members || [{ text: row.text, offset: row.offset ?? null }];
  return {
    localId: crypto.randomUUID(),
    dbId: row.id,
    text: row.text,
    lemma: row.data?.lemma || row.text,
    translation,
    context: row.context || "",
    offset: row.offset ?? null,
    source_url: row.source_url || "",
    clusterMembers,
    timestamp: row.created_at ? new Date(row.created_at).getTime() : 0,
  };
}

export async function seedFromDB(dbRows) {
  const words = await getWords();
  if (words.length > 0) return;
  await setWords(dbRows.map(rowToEntry));
}

export async function seedArchivesFromDB(dbRows) {
  const archives = await getArchives();
  if (archives.length > 0) return;
  await setArchives(dbRows.map(rowToEntry));
}

// ── Broadcast helpers ─────────────────────────────────────────────────────────

export async function broadcastToAllTabs(message, excludeTabId = null) {
  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    if (tab.id && tab.id !== excludeTabId) {
      chrome.tabs.sendMessage(tab.id, message).catch(() => {});
    }
  }
}

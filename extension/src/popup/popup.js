const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

const els = {
  targetLang: $("#targetLang"),
  mode: $("#mode"),
  search: $("#searchInput"),
  wordsList: $("#wordsList"),
  deleteBtn: $("#deleteSelected"),
  selectAllBtn: $("#selectAll"),
  selectedCount: $("#selectedCount"),
  wordCount: $("#wordCount"),
  settingsToggle: $(".settings-toggle"),
  settingsPanel: $(".settings-panel"),
};

let words = [];
let selected = new Set();

// Settings
async function loadSettings() {
  const res = await chrome.runtime.sendMessage({ action: "getSettings" });
  els.targetLang.value = res.targetLang || "en";
  els.mode.value = res.mode || "simple";
}

function saveSettings() {
  chrome.runtime.sendMessage({
    action: "saveSettings",
    data: { targetLang: els.targetLang.value, mode: els.mode.value },
  });
}

// Words
async function loadWords() {
  const { highlights = {} } = await chrome.storage.local.get("highlights");

  const seen = new Set();
  words = Object.entries(highlights)
    .flatMap(([url, items]) => items.map((h) => ({ ...h, url })))
    .reverse()
    .filter((h) => !seen.has(h.text) && seen.add(h.text));

  render();
}

function getFiltered() {
  const q = els.search.value.toLowerCase().trim();
  if (!q) return words;
  return words.filter((w) =>
    w.text.toLowerCase().includes(q) || w.translation.toLowerCase().includes(q)
  );
}

function render() {
  const filtered = getFiltered();
  els.wordCount.textContent = `${filtered.length} word${filtered.length !== 1 ? "s" : ""}`;

  if (!filtered.length) {
    const msg = els.search.value ? "No matches found" : "No translations yet";
    els.wordsList.innerHTML = `
      <div class="words-empty">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 0 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25"/>
        </svg>
        <p>${msg}</p>
      </div>`;
    return;
  }

  els.wordsList.innerHTML = filtered.map((w) => `
    <div class="word-item${selected.has(w.text) ? " selected" : ""}" data-text="${esc(w.text)}">
      <input type="checkbox" class="word-checkbox"${selected.has(w.text) ? " checked" : ""}>
      <div class="word-content">
        <div class="word-header">
          <span class="word-text">${esc(w.text)}</span>
          <svg class="word-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="6 9 12 15 18 9"/>
          </svg>
        </div>
        <div class="word-details">
          <div class="word-translation">${formatTranslation(w.translation)}</div>
          <div class="word-meta">
            <a href="${esc(w.url)}" class="word-link" target="_blank">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                <polyline points="15 3 21 3 21 9"/>
                <line x1="10" y1="14" x2="21" y2="3"/>
              </svg>
              Source
            </a>
          </div>
        </div>
      </div>
    </div>
  `).join("");

  els.wordsList.querySelectorAll(".word-item").forEach((item) => {
    const cb = item.querySelector(".word-checkbox");
    const text = item.dataset.text;

    cb.onclick = (e) => {
      e.stopPropagation();
      cb.checked ? selected.add(text) : selected.delete(text);
      updateSelection();
    };

    item.onclick = (e) => e.target !== cb && item.classList.toggle("expanded");
  });
}

function updateSelection() {
  els.selectedCount.textContent = selected.size;
  els.deleteBtn.classList.toggle("hidden", !selected.size);

  els.wordsList.querySelectorAll(".word-item").forEach((item) => {
    const isSelected = selected.has(item.dataset.text);
    item.classList.toggle("selected", isSelected);
    item.querySelector(".word-checkbox").checked = isSelected;
  });
}

async function deleteSelected() {
  if (!selected.size) return;

  const texts = [...selected];
  const { highlights = {} } = await chrome.storage.local.get("highlights");

  for (const url of Object.keys(highlights)) {
    highlights[url] = highlights[url].filter((h) => !texts.includes(h.text));
    if (!highlights[url].length) delete highlights[url];
  }

  await chrome.storage.local.set({ highlights });

  // Notify content script
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (tab?.id) {
    texts.forEach((text) => chrome.tabs.sendMessage(tab.id, { action: "removeHighlight", text }));
  }

  selected.clear();
  updateSelection();
  loadWords();
}

function toggleSelectAll() {
  const filtered = getFiltered();
  const allSelected = filtered.every((w) => selected.has(w.text));

  filtered.forEach((w) => allSelected ? selected.delete(w.text) : selected.add(w.text));
  updateSelection();
}

// Helpers
const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

function formatTranslation(text) {
  return esc(text)
    .replace(/\*\*([^*]+)\*\*:/g, '<span class="label">$1:</span>')
    .replace(/\n- /g, "\n• ")
    .replace(/\n/g, "<br>");
}

// Events
els.settingsToggle.onclick = () => els.settingsPanel.classList.toggle("hidden");
els.targetLang.onchange = saveSettings;
els.mode.onchange = saveSettings;
els.search.oninput = render;
els.deleteBtn.onclick = deleteSelected;
els.selectAllBtn.onclick = toggleSelectAll;

// Init
loadSettings();
loadWords();

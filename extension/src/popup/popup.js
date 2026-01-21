const targetLangSelect = document.getElementById("targetLang");
const modeSelect = document.getElementById("mode");
const statusEl = document.getElementById("status");

async function loadSettings() {
  const response = await chrome.runtime.sendMessage({ action: "getSettings" });
  targetLangSelect.value = response.targetLang || "en";
  modeSelect.value = response.mode || "simple";
}

async function saveSettings() {
  const settings = {
    targetLang: targetLangSelect.value,
    mode: modeSelect.value,
  };

  await chrome.runtime.sendMessage({ action: "saveSettings", data: settings });

  statusEl.textContent = "Saved";
  setTimeout(() => {
    statusEl.textContent = "";
  }, 1500);
}

targetLangSelect.addEventListener("change", saveSettings);
modeSelect.addEventListener("change", saveSettings);

loadSettings();

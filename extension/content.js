const API_URL = "http://localhost:8000";

let button = null;
let tooltip = null;

document.addEventListener("mouseup", (e) => {
  // Ignore clicks on our own elements
  if (button && button.contains(e.target)) return;
  if (tooltip && tooltip.contains(e.target)) return;

  const selection = window.getSelection();
  const text = selection.toString().trim();

  removeButton();
  removeTooltip();

  if (text.length > 0 && text.length < 500) {
    showButton(e.pageX, e.pageY, text);
  }
});

document.addEventListener("mousedown", (e) => {
  if (button && !button.contains(e.target)) {
    removeButton();
  }
  if (tooltip && !tooltip.contains(e.target)) {
    removeTooltip();
  }
});

function showButton(x, y, text) {
  button = document.createElement("button");
  button.className = "contxtly-btn";
  button.textContent = "Translate";
  button.style.left = `${x}px`;
  button.style.top = `${y + 10}px`;

  button.addEventListener("click", () => {
    translate(text, x, y);
    removeButton();
  });

  document.body.appendChild(button);
}

function removeButton() {
  if (button) {
    button.remove();
    button = null;
  }
}

function removeTooltip() {
  if (tooltip) {
    tooltip.remove();
    tooltip = null;
  }
}

async function translate(text, x, y) {
  tooltip = document.createElement("div");
  tooltip.className = "contxtly-tooltip contxtly-tooltip-loading";
  tooltip.textContent = "Translating...";
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y + 10}px`;
  document.body.appendChild(tooltip);

  try {
    const res = await fetch(`${API_URL}/translate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: text,
        target_lang: "en",
        mode: "simple",
      }),
    });

    if (!res.ok) throw new Error("API error");

    const data = await res.json();
    tooltip.className = "contxtly-tooltip";
    tooltip.textContent = data.translation;
  } catch (err) {
    tooltip.className = "contxtly-tooltip contxtly-tooltip-error";
    tooltip.textContent = "Translation failed";
  }
}

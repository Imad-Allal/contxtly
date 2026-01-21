let button = null;
let tooltip = null;

export function showButton(x, y, onClick) {
  removeButton();

  button = document.createElement("button");
  button.className = "contxtly-btn";
  button.textContent = "Translate";

  const pos = clampPosition(x, y + 10, 100, 36);
  button.style.left = `${pos.x}px`;
  button.style.top = `${pos.y}px`;

  button.addEventListener("click", (e) => {
    e.stopPropagation();
    onClick();
    removeButton();
  });

  document.body.appendChild(button);
}

export function removeButton() {
  if (button) {
    button.remove();
    button = null;
  }
}

export function showTooltip(x, y) {
  removeTooltip();

  tooltip = document.createElement("div");
  tooltip.className = "contxtly-tooltip contxtly-tooltip-loading";
  tooltip.textContent = "Translating...";

  const pos = clampPosition(x, y + 10, 320, 100);
  tooltip.style.left = `${pos.x}px`;
  tooltip.style.top = `${pos.y}px`;

  document.body.appendChild(tooltip);
  return tooltip;
}

export function updateTooltip(content, isError = false) {
  if (!tooltip) return;

  tooltip.className = isError
    ? "contxtly-tooltip contxtly-tooltip-error"
    : "contxtly-tooltip";

  if (isError) {
    tooltip.textContent = content;
    return;
  }

  tooltip.innerHTML = formatTranslation(content);
}

function formatTranslation(text) {
  const sections = {
    Translation: "",
    Meaning: "",
    Breakdown: "",
    Example: "",
  };

  let currentSection = null;
  const lines = text.split("\n");

  for (const line of lines) {
    const match = line.match(/^\*\*(\w+)\*\*:\s*(.*)$/);
    if (match) {
      currentSection = match[1];
      if (sections.hasOwnProperty(currentSection)) {
        sections[currentSection] = match[2];
      }
    } else if (currentSection === "Example" && line.trim().startsWith("-")) {
      sections.Example += line.trim() + "\n";
    } else if (currentSection && line.trim()) {
      sections[currentSection] += " " + line.trim();
    }
  }

  let html = "";

  if (sections.Translation) {
    html += `<div class="contxtly-section contxtly-translation">${escapeHtml(sections.Translation.trim())}</div>`;
  }

  if (sections.Meaning) {
    html += `<div class="contxtly-section contxtly-meaning">${escapeHtml(sections.Meaning.trim())}</div>`;
  }

  if (sections.Breakdown && isValidBreakdown(sections.Breakdown.trim())) {
    html += `<div class="contxtly-section contxtly-breakdown">${escapeHtml(sections.Breakdown.trim())}</div>`;
  }

  if (sections.Example) {
    const exampleLines = sections.Example.trim()
      .split("\n")
      .filter((line) => line.trim())
      .map((line) => escapeHtml(line.replace(/^-\s*/, "")));

    if (exampleLines.length >= 2) {
      // First line is source, second is translation
      html += `<div class="contxtly-section contxtly-example">
        <div class="contxtly-example-source">${exampleLines[0]}</div>
        <div class="contxtly-example-translation">${exampleLines[1]}</div>
      </div>`;
    } else if (exampleLines.length === 1) {
      html += `<div class="contxtly-section contxtly-example">${exampleLines[0]}</div>`;
    }
  }

  return html || escapeHtml(text);
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

function isValidBreakdown(text) {
  // Must contain actual breakdown pattern: "word (meaning) + word (meaning)"
  // or "word (meaning) = translation"
  return /\(.+\)\s*[+=]/.test(text) || /[+=]\s*\(.+\)/.test(text);
}

export function removeTooltip() {
  if (tooltip) {
    tooltip.remove();
    tooltip = null;
  }
}

export function isOwnElement(el) {
  return (button && button.contains(el)) || (tooltip && tooltip.contains(el));
}

function clampPosition(x, y, width, height) {
  const maxX = window.innerWidth - width - 10;
  const maxY = window.innerHeight - height - 10;

  return {
    x: Math.max(10, Math.min(x, maxX)),
    y: Math.max(10, Math.min(y, maxY)),
  };
}

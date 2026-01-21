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
  tooltip.textContent = content;
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

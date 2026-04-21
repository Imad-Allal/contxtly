import { useEffect } from "react";

export interface ShortcutHandlers {
  onFocusSearch?: () => void;
  onToggleTrash?: () => void;
  onReviewTab?: () => void;
  onListTab?: () => void;
  onStatsTab?: () => void;
  onExport?: () => void;
  onEscape?: () => void;
  onHelp?: () => void;
}

function isTextInput(el: EventTarget | null): boolean {
  if (!(el instanceof HTMLElement)) return false;
  const tag = el.tagName.toLowerCase();
  return tag === "input" || tag === "textarea" || el.isContentEditable;
}

export function useShortcuts(h: ShortcutHandlers, enabled = true) {
  useEffect(() => {
    if (!enabled) return;

    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") {
        h.onEscape?.();
        return;
      }

      if (isTextInput(e.target) && e.key !== "Escape") return;
      if (e.ctrlKey || e.metaKey || e.altKey) return;

      switch (e.key) {
        case "/":
          e.preventDefault();
          h.onFocusSearch?.();
          break;
        case "t":
          h.onToggleTrash?.();
          break;
        case "r":
          h.onReviewTab?.();
          break;
        case "l":
          h.onListTab?.();
          break;
        case "s":
          h.onStatsTab?.();
          break;
        case "e":
          h.onExport?.();
          break;
        case "?":
          h.onHelp?.();
          break;
      }
    }

    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [h, enabled]);
}

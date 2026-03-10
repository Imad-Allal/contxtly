import { useState, useCallback, useMemo } from "react";
import type { Word } from "../types";

export function getWordKey(word: Word): string {
  return word.lemma || word.text;
}

export function useWordSelection(filtered: Word[]) {
  const [selected, setSelected] = useState<Set<string>>(new Set());

  const allSelected =
    filtered.length > 0 &&
    filtered.every((w) => selected.has(getWordKey(w)));

  const toggleSelect = useCallback((key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }, []);

  const toggleSelectAll = useCallback(() => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (filtered.every((w) => prev.has(getWordKey(w)))) {
        filtered.forEach((w) => next.delete(getWordKey(w)));
      } else {
        filtered.forEach((w) => next.add(getWordKey(w)));
      }
      return next;
    });
  }, [filtered]);

  const clearSelection = useCallback(() => setSelected(new Set()), []);

  return { selected, allSelected, toggleSelect, toggleSelectAll, clearSelection };
}

export function useWordFilter(words: Word[], search: string) {
  return useMemo(() => {
    const q = search.toLowerCase().trim();
    if (!q) return words;
    return words.filter((w) => {
      const display = getWordKey(w).toLowerCase();
      if (display.includes(q)) return true;
      const t = w.translation;
      if (typeof t === "object" && t !== null) {
        return (
          (t.translation || "").toLowerCase().includes(q) ||
          (t.meaning || "").toLowerCase().includes(q)
        );
      }
      return String(t).toLowerCase().includes(q);
    });
  }, [words, search]);
}

export function useExpandedWords() {
  const [expandedWords, setExpandedWords] = useState<Set<string>>(new Set());

  const toggleExpand = useCallback((key: string) => {
    setExpandedWords((prev) => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  }, []);

  return { expandedWords, toggleExpand };
}

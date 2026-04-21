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

export type WordTypeFilter = "all" | "noun" | "verb" | "collocation" | "expression" | "other";

function getTypeGroup(word: Word): WordTypeFilter {
  const t = word.translation;
  if (typeof t !== "object" || t === null) return "other";
  const wt = t.word_type;
  if (!wt) return t.collocation_pattern ? "collocation" : "other";
  if (wt === "noun" || wt === "plural_noun") return "noun";
  if (wt === "conjugated_verb" || wt === "separable_prefix") return "verb";
  if (wt === "collocation_verb" || wt === "collocation_prep") return "collocation";
  if (wt === "fixed_expression") return "expression";
  return "other";
}

export function useWordFilter(words: Word[], search: string, typeFilter: WordTypeFilter = "all") {
  return useMemo(() => {
    let result = words;

    if (typeFilter !== "all") {
      result = result.filter((w) => getTypeGroup(w) === typeFilter);
    }

    const q = search.toLowerCase().trim();
    if (!q) return result;

    return result.filter((w) => {
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
  }, [words, search, typeFilter]);
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

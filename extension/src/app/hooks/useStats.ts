import { useMemo } from "react";
import type { Word, TranslationData } from "../types";
import type { WordTypeColorKey } from "../theme";

const WORD_TYPE_MAP: Record<string, Exclude<WordTypeColorKey, "verb_modal" | "verb_compound">> = {
  conjugated_verb: "verb", separable_prefix: "verb", verb: "verb",
  noun: "noun", plural_noun: "noun",
  adjective: "adjective",
  collocation_verb: "collocation", collocation_prep: "collocation", collocation: "collocation",
  fixed_expression: "expression", expression: "expression",
  compound: "compound",
};

type StatKey = Exclude<WordTypeColorKey, "verb_modal" | "verb_compound"> | "other";

function typeOf(w: Word): StatKey {
  const t = typeof w.translation === "object" ? (w.translation as TranslationData) : null;
  if (!t) return "other";
  if (t.word_type && WORD_TYPE_MAP[t.word_type]) return WORD_TYPE_MAP[t.word_type];
  if (t.collocation_pattern) return "collocation";
  return "other";
}

function dayKey(ts: number): string {
  const d = new Date(ts);
  return `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
}

export interface Stats {
  total: number;
  streak: number;
  byType: Record<Exclude<WordTypeColorKey, "verb_modal" | "verb_compound"> | "other", number>;
  last14: { day: string; count: number; label: string }[];
}

export function useStats(words: Word[]): Stats {
  return useMemo(() => {
    const byType: Stats["byType"] = {
      verb: 0, noun: 0, adjective: 0, collocation: 0, expression: 0, compound: 0, other: 0,
    };
    const perDay = new Map<string, number>();
    for (const w of words) {
      byType[typeOf(w)]++;
      if (w.timestamp) {
        const k = dayKey(w.timestamp);
        perDay.set(k, (perDay.get(k) ?? 0) + 1);
      }
    }

    const last14: Stats["last14"] = [];
    const now = new Date();
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now);
      d.setDate(d.getDate() - i);
      const key = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
      last14.push({
        day: key,
        count: perDay.get(key) ?? 0,
        label: d.toLocaleDateString(undefined, { weekday: "short" }),
      });
    }

    let streak = 0;
    const today = new Date();
    for (let i = 0; i < 365; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const key = `${d.getFullYear()}-${d.getMonth() + 1}-${d.getDate()}`;
      if ((perDay.get(key) ?? 0) > 0) streak++;
      else if (i > 0) break;
    }

    return { total: words.length, streak, byType, last14 };
  }, [words]);
}

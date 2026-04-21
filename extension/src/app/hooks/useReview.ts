import { useEffect, useState, useCallback, useMemo } from "react";
import type { Word } from "../types";
import { getWordKey } from "./useWords";

const STORAGE_KEY = "review_state";
const DAY = 86_400_000;

export type Grade = "again" | "hard" | "good" | "easy";

export interface ReviewEntry {
  ease: number;
  interval: number;
  repetitions: number;
  lastReviewedAt: number;
  dueAt: number;
}

type State = Record<string, ReviewEntry>;

function defaultEntry(now: number): ReviewEntry {
  return { ease: 2.5, interval: 0, repetitions: 0, lastReviewedAt: 0, dueAt: now };
}

function applyGrade(entry: ReviewEntry, grade: Grade, now: number): ReviewEntry {
  let { ease, interval, repetitions } = entry;
  switch (grade) {
    case "again":
      repetitions = 0;
      interval = 1;
      ease = Math.max(1.3, ease - 0.2);
      break;
    case "hard":
      repetitions += 1;
      interval = Math.max(1, Math.round((interval || 1) * 1.2));
      ease = Math.max(1.3, ease - 0.15);
      break;
    case "good":
      repetitions += 1;
      interval = repetitions === 1 ? 1 : repetitions === 2 ? 3 : Math.round(interval * ease);
      break;
    case "easy":
      repetitions += 1;
      interval = repetitions === 1 ? 2 : Math.round((interval || 1) * ease * 1.3);
      ease = ease + 0.15;
      break;
  }
  return {
    ease,
    interval,
    repetitions,
    lastReviewedAt: now,
    dueAt: now + interval * DAY,
  };
}

export function useReview(words: Word[]) {
  const [state, setState] = useState<State>({});
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    chrome.storage.local.get(STORAGE_KEY).then((r) => {
      setState((r[STORAGE_KEY] as State) ?? {});
      setLoaded(true);
    });
  }, []);

  const persist = useCallback(async (next: State) => {
    setState(next);
    await chrome.storage.local.set({ [STORAGE_KEY]: next });
  }, []);

  const due = useMemo(() => {
    if (!loaded) return [];
    const now = Date.now();
    return words.filter((w) => {
      const key = getWordKey(w);
      const e = state[key];
      if (!e) return true;
      return e.dueAt <= now;
    });
  }, [words, state, loaded]);

  const grade = useCallback(async (word: Word, g: Grade) => {
    const key = getWordKey(word);
    const now = Date.now();
    const current = state[key] ?? defaultEntry(now);
    const next = applyGrade(current, g, now);
    await persist({ ...state, [key]: next });
  }, [state, persist]);

  return { due, grade, loaded };
}

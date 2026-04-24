import { useEffect, useState, useCallback, useMemo } from "react";
import type { Word } from "../types";
import { getWordKey } from "./useWords";

const STORAGE_KEY = "review_state";
const MIN = 60_000;
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
  let dueDelta: number;
  switch (grade) {
    case "again":
      repetitions = 0;
      interval = 0;
      ease = Math.max(1.3, ease - 0.2);
      dueDelta = 1 * MIN;
      break;
    case "hard":
      ease = Math.max(1.3, ease - 0.15);
      if (repetitions < 1) {
        dueDelta = 6 * MIN;
      } else {
        interval = Math.max(1, Math.round((interval || 1) * 1.2));
        dueDelta = interval * DAY;
      }
      repetitions += 1;
      break;
    case "good":
      repetitions += 1;
      if (repetitions === 1) {
        dueDelta = 10 * MIN;
      } else if (repetitions === 2) {
        interval = 1;
        dueDelta = interval * DAY;
      } else {
        interval = Math.round((interval || 1) * ease);
        dueDelta = interval * DAY;
      }
      break;
    case "easy":
      repetitions += 1;
      interval = repetitions === 1 ? 4 : Math.round((interval || 1) * ease * 1.3);
      ease = ease + 0.15;
      dueDelta = interval * DAY;
      break;
  }
  return {
    ease,
    interval,
    repetitions,
    lastReviewedAt: now,
    dueAt: now + dueDelta,
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
      const wordCount = (w.text || "").trim().split(/\s+/).filter(Boolean).length;
      if (wordCount > 3) return false;
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

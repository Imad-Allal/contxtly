import { useEffect, useState, useCallback } from "react";

const STORAGE_KEY = "onboarded";

export function useOnboarding(loggedIn: boolean) {
  const [onboarded, setOnboarded] = useState<boolean | null>(null);
  const [showLangNotice, setShowLangNotice] = useState(false);

  useEffect(() => {
    if (!loggedIn) {
      setOnboarded(null);
      return;
    }
    chrome.storage.local.get(STORAGE_KEY).then((res) => {
      setOnboarded(!!res[STORAGE_KEY]);
    });
  }, [loggedIn]);

  const finish = useCallback(async () => {
    await chrome.storage.local.set({ [STORAGE_KEY]: true });
    setOnboarded(true);
    setShowLangNotice(true);
  }, []);

  const dismissLangNotice = useCallback(() => setShowLangNotice(false), []);

  const replay = useCallback(async () => {
    await chrome.storage.local.set({ [STORAGE_KEY]: false });
    setOnboarded(false);
  }, []);

  const showOverlay = loggedIn && onboarded === false;

  return { showOverlay, finish, replay, showLangNotice, dismissLangNotice };
}

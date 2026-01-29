import hashlib
import logging
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class CachedTranslation:
    translation: str
    meaning: str | None
    breakdown: str | None
    context_translation: dict | None  # {"source": ..., "target": ...}


class TranslationCache:
    def __init__(self):
        self._words: dict[str, CachedTranslation] = {}  # word+context → full result
        self._contexts: dict[str, str] = {}  # context → translated context

    def _word_key(self, word: str, context: str, source_lang: str, target_lang: str) -> str:
        normalized = f"{word.lower()}:{' '.join(context.lower().split())}:{source_lang}:{target_lang}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _context_key(self, context: str, source_lang: str, target_lang: str) -> str:
        normalized = f"{' '.join(context.lower().split())}:{source_lang}:{target_lang}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get(self, word: str, context: str, source_lang: str, target_lang: str) -> CachedTranslation | None:
        return self._words.get(self._word_key(word, context, source_lang, target_lang))

    def get_context(self, context: str, source_lang: str, target_lang: str) -> str | None:
        return self._contexts.get(self._context_key(context, source_lang, target_lang))

    def set(self, word: str, context: str, source_lang: str, target_lang: str, data: CachedTranslation) -> None:
        self._words[self._word_key(word, context, source_lang, target_lang)] = data
        if context and data.context_translation:
            self._contexts[self._context_key(context, source_lang, target_lang)] = data.context_translation["target"]
        log.info(f"[CACHE] Stored '{word}'")

    def stats(self) -> dict:
        return {"words": len(self._words), "contexts": len(self._contexts)}

    def clear(self) -> None:
        self._words.clear()
        self._contexts.clear()
        log.info("[CACHE] Cleared")


cache = TranslationCache()

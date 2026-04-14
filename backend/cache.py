import hashlib
import json
import logging
from dataclasses import asdict, dataclass

import redis

from config import settings

log = logging.getLogger(__name__)

WORD_TTL = 60 * 60 * 24      # 24 hours
CONTEXT_TTL = 60 * 60        # 1 hour

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


@dataclass
class CachedTranslation:
    translation: str
    meaning: str | None
    breakdown: str | None
    context_translation: dict | None  # {"source": ..., "target": ...}
    lemma: str | None = None
    related_words: list | None = None
    collocation_pattern: str | None = None
    word_type: str | None = None


class TranslationCache:
    def _word_key(self, word: str, context: str, source_lang: str, target_lang: str) -> str:
        normalized = f"{word.lower()}:{' '.join(context.lower().split())}:{source_lang}:{target_lang}"
        return "word:" + hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def _context_key(self, context: str, source_lang: str, target_lang: str) -> str:
        normalized = f"{' '.join(context.lower().split())}:{source_lang}:{target_lang}"
        return "ctx:" + hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def get(self, word: str, context: str, source_lang: str, target_lang: str) -> CachedTranslation | None:
        raw = get_redis().get(self._word_key(word, context, source_lang, target_lang))
        if raw is None:
            return None
        return CachedTranslation(**json.loads(raw))

    def get_context(self, context: str, source_lang: str, target_lang: str) -> str | None:
        return get_redis().get(self._context_key(context, source_lang, target_lang))

    def set(self, word: str, context: str, source_lang: str, target_lang: str, data: CachedTranslation) -> None:
        r = get_redis()
        r.set(self._word_key(word, context, source_lang, target_lang), json.dumps(asdict(data)), ex=WORD_TTL)
        if context and data.context_translation:
            r.set(self._context_key(context, source_lang, target_lang), data.context_translation["target"], ex=CONTEXT_TTL)
        log.info(f"[CACHE] Stored '{word}'")

    def stats(self) -> dict:
        r = get_redis()
        word_count = len(r.keys("word:*"))
        ctx_count = len(r.keys("ctx:*"))
        return {"words": word_count, "contexts": ctx_count}

    def clear(self) -> None:
        r = get_redis()
        word_keys = r.keys("word:*")
        ctx_keys = r.keys("ctx:*")
        if word_keys:
            r.delete(*word_keys)
        if ctx_keys:
            r.delete(*ctx_keys)
        log.info("[CACHE] Cleared")


cache = TranslationCache()

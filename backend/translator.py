import json
import logging
import time
from groq import Groq, InternalServerError, BadRequestError

from config import settings
from prompts.word_translation import (
    build_simple_translation_prompt,
    build_word_translation_prompt,
)
from timing import record_timing

log = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

# Models
PRIMARY_MODEL = "openai/gpt-oss-120b"
FALLBACK_MODEL = "openai/gpt-oss-20b"  # Fallback model in case of 503 errors


def llm_call(prompt: str, model: str = PRIMARY_MODEL, json_mode: bool = True) -> dict | str:
    """Make an LLM call with optional JSON mode. Falls back to FALLBACK_MODEL on 503."""
    log.debug(f"[LLM] Calling {model}, json_mode={json_mode}")
    log.debug(f"[LLM] Prompt: {prompt[:100]}...")

    models_to_try = [model, FALLBACK_MODEL] if model != FALLBACK_MODEL else [model]

    for attempt_model in models_to_try:
        try:
            start = time.perf_counter()
            response = client.chat.completions.create(
                model=attempt_model,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"} if json_mode else None,
                temperature=0.2,
                max_tokens=500,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000
            record_timing(f"LLM API call ({attempt_model})", elapsed_ms)
            content = response.choices[0].message.content.strip()
            log.debug(f"[LLM] Raw response: {content[:200]}...")

            if json_mode:
                try:
                    parsed = json.loads(content)
                    log.debug(f"[LLM] Parsed JSON: {parsed}")
                    return parsed
                except json.JSONDecodeError as e:
                    log.error(f"[LLM] JSON parse error: {e}")
                    return {"error": "Invalid JSON response", "raw": content}

            return content

        except (InternalServerError, BadRequestError) as e:
            if attempt_model != FALLBACK_MODEL:
                log.warning(f"[LLM] {attempt_model} failed ({type(e).__name__}), falling back to {FALLBACK_MODEL}")
            else:
                log.error(f"[LLM] Fallback model also failed: {e}")
                raise

    raise RuntimeError("All models failed")


def translate_smart(
    word: str,
    source_lang: str,
    target_lang: str,
    context: str = "",
    lemma: str | None = None,
    skip_context_translation: bool = False,
    compound_parts: list[str] | None = None,
    collocation_pattern: str | None = None,
    modal_verb: str | None = None,
    pos: str | None = None,
) -> dict:
    """
    Combined translation: word + meaning + base form + context translation + compound parts in one LLM call.

    Returns:
        {
            "translation": str,
            "meaning": str,
            "base_translation": str | None,
            "context_translation": str | None,
            "compound_parts": [("part", "base", "translation"), ...] | None,
            "modal_translation": str | None,
        }
    """
    log.info(f"[TRANSLATE] translate_smart('{word}', {source_lang} -> {target_lang}, lemma={lemma}, collocation={collocation_pattern})")

    prompt = build_word_translation_prompt(
        word=word,
        source_lang=source_lang,
        target_lang=target_lang,
        context=context,
        lemma=lemma,
        skip_context_translation=skip_context_translation,
        compound_parts=compound_parts,
        collocation_pattern=collocation_pattern,
        modal_verb=modal_verb,
        pos=pos,
    )

    result = llm_call(prompt, model=PRIMARY_MODEL)

    if isinstance(result, dict):
        translated_parts = None
        if compound_parts:
            parts = result.get("parts", [])
            if parts:
                translated_parts = [
                    (p.get("part", ""), p.get("base", p.get("part", "")), p.get("translation", ""))
                    for p in parts if isinstance(p, dict)
                ]
                log.info(f"[TRANSLATE] Compound parts: {translated_parts}")

        output = {
            "translation": result.get("translation", word),
            "meaning": result.get("meaning", ""),
            "base_translation": result.get("base_translation"),
            "context_translation": result.get("context_translation"),
            "compound_parts": translated_parts,
            "modal_translation": result.get("modal_translation"),
        }
        log.info(f"[TRANSLATE] Smart result: {output}")
        return output

    log.warning(f"[TRANSLATE] Unexpected result type: {type(result)}")
    return {
        "translation": word,
        "meaning": "",
        "base_translation": None,
        "context_translation": None,
        "compound_parts": None,
        "modal_translation": None,
    }


def translate_simple(word: str, source_lang: str, target_lang: str) -> str:
    """Simple translation - just the translated word."""
    log.info(f"[TRANSLATE] translate_simple('{word}' -> {target_lang})")
    prompt = build_simple_translation_prompt(word, source_lang, target_lang)
    result = llm_call(prompt, model=PRIMARY_MODEL)
    log.info(f"[TRANSLATE] Simple result: '{result}'")
    return result

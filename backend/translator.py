import json
import logging
import time
from groq import Groq

from config import settings
from timing import record_timing

log = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

# Models
SIMPLE_MODEL = "llama-3.1-8b-instant"
SMART_MODEL = "llama-3.3-70b-versatile"


def llm_call(prompt: str, model: str = SMART_MODEL, json_mode: bool = True) -> dict | str:
    """Make an LLM call with optional JSON mode."""
    log.debug(f"[LLM] Calling {model}, json_mode={json_mode}")
    log.debug(f"[LLM] Prompt: {prompt[:100]}...")

    start = time.perf_counter()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"} if json_mode else None,
        temperature=0.2,
        max_tokens=500,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000
    record_timing(f"LLM API call ({model})", elapsed_ms)
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


def translate_smart(
    word: str,
    source_lang: str,
    target_lang: str,
    context: str = "",
    lemma: str | None = None,
    skip_context_translation: bool = False,
    compound_parts: list[str] | None = None,
    collocation_pattern: str | None = None,
) -> dict:
    """
    Combined translation: word + meaning + base form + context translation + compound parts in one LLM call.

    Args:
        word: The word to translate
        source_lang: Source language code
        target_lang: Target language code
        context: Sentence context for accurate translation (will be translated too)
        lemma: Base form of word (if different from word)
        skip_context_translation: Skip translating context (if already cached)
        compound_parts: Pre-split compound parts to translate (e.g., ["Kranken", "Haus"])
        collocation_pattern: Verb+preposition pattern (e.g., "von etwas ausgehen")

    Returns:
        {
            "translation": str,
            "meaning": str,
            "base_translation": str | None,
            "context_translation": str | None,
            "compound_parts": [("part", "base", "translation"), ...] | None,
        }
    """
    log.info(f"[TRANSLATE] translate_smart('{word}', {source_lang} -> {target_lang}, lemma={lemma}, collocation={collocation_pattern})")

    context_instruction = ""
    if context:
        context_instruction = f'The word appears in this sentence: "{context}"'

    collocation_instruction = ""
    if collocation_pattern:
        collocation_instruction = f"""
CRITICAL: The word is part of the verb+preposition collocation "{collocation_pattern}".
You must translate the COLLOCATION as a whole, giving the natural IDIOMATIC equivalent in {target_lang} — NOT a word-for-word literal translation.
Examples of correct idiomatic translations:
- "von etwas ausgehen" → French: "partir du principe que / supposer / estimer" (NOT "partir de")
- "von jemandem etwas erwarten" → French: "s'attendre à quelque chose de la part de quelqu'un" (NOT "prévoir" or "attendre")
- "auf etwas ankommen" → French: "dépendre de" (NOT "arriver sur")
Apply the same principle: find the natural {target_lang} expression that carries the same meaning as the German collocation.
The context_translation MUST also use this idiomatic equivalent, not a literal rendering."""

    lemma_instruction = ""
    if lemma and lemma != word:
        lemma_instruction = f'\nAlso translate the base form "{lemma}" separately.'

    compound_instruction = ""
    if compound_parts:
        parts_str = ", ".join(f'"{p}"' for p in compound_parts)
        compound_instruction = f'\nThese are the EXACT compound word parts (do NOT split them further): {parts_str}. For each part, find its dictionary form and translate it. Keep nouns as nouns (e.g., "Gesundheit" stays "Gesundheit", not "gesund"). Only simplify declined/genitive forms (e.g., "Auslands" → "Ausland", "Kranken" → "krank"). Return exactly {len(compound_parts)} parts.'

    prompt = f"""Translate "{word}" from {source_lang} to {target_lang}.
{context_instruction}
{collocation_instruction}
{lemma_instruction}
{compound_instruction}

Return JSON with:
- translation: {"the idiomatic translation of the COLLOCATION in " + target_lang + " (e.g., the full verbal phrase like 's''attendre à')" if collocation_pattern else "the context-appropriate translation in " + target_lang + " (MUST match the meaning used in the context sentence, not just the most common dictionary definition)"}
- meaning: explain what the word means IN THIS SPECIFIC CONTEXT (one sentence in {target_lang})
- base_translation: translation of the base form "{lemma}" (only if base form was provided, otherwise null){"" if skip_context_translation else f"""
- context_translation: full translation of the context sentence to {target_lang} (only if context was provided, otherwise null)"""}{'''
- parts: array of objects with "part" (original), "base" (lemma/base form), and "translation" (translation of base form) for each compound part (only if compound parts were provided)''' if compound_parts else ''}

Return ONLY valid JSON."""

    result = llm_call(prompt, model=SMART_MODEL)

    if isinstance(result, dict):
        # Parse compound parts: (original_part, base_form, translation)
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
    }


def translate_simple(word: str, source_lang: str, target_lang: str) -> str:
    """Simple translation - just the translated word."""
    log.info(f"[TRANSLATE] translate_simple('{word}' -> {target_lang})")
    prompt = f"""Translate {word} from {source_lang} to {target_lang}. Return ONLY the translation, nothing else.\n\n{word}

Return JSON with:
- translation: the equivalent word/phrase in {target_lang}

Return ONLY valid JSON."""

    result = llm_call(prompt, model=SIMPLE_MODEL)
    log.info(f"[TRANSLATE] Simple result: '{result}'")
    return result

import json
import logging
import time
from groq import Groq, InternalServerError, BadRequestError

from config import settings
from timing import record_timing

log = logging.getLogger(__name__)

client = Groq(api_key=settings.groq_api_key)

# Models
PRIMARY_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
FALLBACK_MODEL = "llama-3.3-70b-versatile"


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

    pos_map = {
        "DET": "determiner/article",
        "PRON": "pronoun",
        "VERB": "verb",
        "NOUN": "noun",
        "ADJ": "adjective",
        "ADV": "adverb",
        "ADP": "preposition",
        "CONJ": "conjunction",
        "CCONJ": "coordinating conjunction",
        "SCONJ": "subordinating conjunction",
        "PART": "particle",
        "NUM": "numeral",
        "INTJ": "interjection",
    }
    pos_instruction = ""
    if pos and pos in pos_map:
        pos_instruction = f'The word "{word}" is a {pos_map[pos]}. '

    context_instruction = ""
    if context:
        context_instruction = f'{pos_instruction}The word appears in this sentence: "{context}"'
    elif pos_instruction:
        context_instruction = pos_instruction.rstrip()

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
        lemma_instruction = f'\nAlso translate the base form (infinitive) "{lemma}" separately. Give the correct, natural dictionary translation — not a transliteration or invented word.'

    modal_instruction = ""
    if modal_verb:
        modal_instruction = f'\nAlso translate the modal verb "{modal_verb}" as used in the context sentence. Give the conjugated translation matching the person/tense in context (e.g., "will" → "veut", "kann" → "peut", "muss" → "doit"), NOT the infinitive.'

    compound_instruction = ""
    if compound_parts:
        parts_str = ", ".join(f'"{p}"' for p in compound_parts)
        compound_instruction = f'\nThese are the EXACT compound word parts (do NOT split them further): {parts_str}. For each part, find its dictionary form and translate it. Keep nouns as nouns (e.g., "Gesundheit" stays "Gesundheit", not "gesund"). Only simplify declined/genitive forms (e.g., "Auslands" → "Ausland", "Kranken" → "krank"). Return exactly {len(compound_parts)} parts.'

    prompt = f"""Translate "{word}" from {source_lang} to {target_lang}.
{context_instruction}
{collocation_instruction}
{lemma_instruction}
{modal_instruction}
{compound_instruction}

Return JSON with:
- translation: {"the idiomatic translation of the COLLOCATION in " + target_lang + " (e.g., the full verbal phrase like 's''attendre à')" if collocation_pattern else "the SHORT, CONCISE dictionary translation of the word itself in " + target_lang + " — 1 to 4 words maximum, like a dictionary entry (e.g. 'être disponible', 'partir', 'maison'). Do NOT use the context sentence to build a phrase. Translate the WORD, not the sentence."}
- meaning: one sentence in {target_lang} explaining what "{word}" means IN THIS SPECIFIC CONTEXT (use the context sentence to explain, but keep it concise)
- base_translation: translation of the base form "{lemma}" (only if base form was provided, otherwise null){"" if skip_context_translation else f"""
- context_translation: full translation of the context sentence to {target_lang}. MUST be a real translation, NOT the original German text. If context was not provided, use null."""}{f'''
- modal_translation: conjugated translation of "{modal_verb}" matching the person/tense in context (e.g., "will" → "veut", "kann" → "peut", "muss" → "doit"). NEVER give the infinitive form.''' if modal_verb else ''}{'''
- parts: array of objects with "part" (original), "base" (lemma/base form), and "translation" (translation of base form) for each compound part (only if compound parts were provided)''' if compound_parts else ''}

Return ONLY valid JSON. Do not use guillemets (« »), curly quotes, or any special punctuation inside JSON string values — use only plain straight quotes for quoting words within strings."""

    result = llm_call(prompt, model=PRIMARY_MODEL)

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
    prompt = f"""Translate {word} from {source_lang} to {target_lang}. Return ONLY the translation, nothing else.\n\n{word}

Return JSON with:
- translation: the equivalent word/phrase in {target_lang}

Return ONLY valid JSON. Do not use guillemets (« »), curly quotes, or any special punctuation inside JSON string values — use only plain straight quotes for quoting words within strings."""

    result = llm_call(prompt, model=PRIMARY_MODEL)
    log.info(f"[TRANSLATE] Simple result: '{result}'")
    return result

import json
import logging
import time
from groq import Groq

from config import settings
from languages import get_language
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


def translate_word(
    word: str,
    source_lang: str,
    target_lang: str,
    context: str = "",
) -> dict:
    """
    Translate a word with meaning.

    Returns:
        {"translation": str, "meaning": str}
    """
    log.info(f"[TRANSLATE] translate_word('{word}', {source_lang} -> {target_lang})")

    context_instruction = ""
    if context:
        context_instruction = f'\nThe word appears in this sentence: "{context}"'

        # Add language-specific prompt additions
        lang_module = get_language(source_lang)
        if lang_module and lang_module.config.translation_prompt_addition:
            context_instruction += lang_module.config.translation_prompt_addition.format(word=word)

    prompt = f"""Translate "{word}" from {source_lang} to {target_lang}.
{context_instruction}

Return JSON with:
- translation: the equivalent word/phrase in {target_lang}
- meaning: explain what the word means IN THIS SPECIFIC CONTEXT (one sentence in {target_lang})

Return ONLY valid JSON."""

    result = llm_call(prompt, model=SMART_MODEL)

    # Ensure required fields
    if isinstance(result, dict):
        output = {
            "translation": result.get("translation", word),
            "meaning": result.get("meaning", ""),
        }
        log.info(f"[TRANSLATE] Result: {output}")
        return output

    log.warning(f"[TRANSLATE] Unexpected result type: {type(result)}")
    return {"translation": word, "meaning": ""}


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


def generate_example(
    word: str,
    source_lang: str,
    target_lang: str,
    meaning: str = "",
) -> dict:
    """
    Generate an example sentence using the word with the same meaning as in context.

    Returns:
        {"source": str, "target": str}
    """
    log.info(f"[EXAMPLE] Generating example for '{word}' in {source_lang}")

    meaning_instruction = ""
    if meaning:
        meaning_instruction = f'The word means: "{meaning}". Use this SAME meaning in the example.'

    prompt = f"""Give one short example sentence using "{word}" in {source_lang}.
{meaning_instruction}
Then translate that sentence to {target_lang}.

Return JSON with:
- source: the example sentence in {source_lang}
- target: the translation in {target_lang}

Return ONLY valid JSON."""

    result = llm_call(prompt, model=SMART_MODEL)

    if isinstance(result, dict):
        output = {
            "source": result.get("source", result.get("example_source", "")),
            "target": result.get("target", result.get("example_target", "")),
        }
        log.info(f"[EXAMPLE] Result: {output}")
        return output

    log.warning(f"[EXAMPLE] Unexpected result type: {type(result)}")
    return {"source": "", "target": ""}


def translate_compound_parts(parts: list[str], source_lang: str, target_lang: str) -> list[tuple[str, str]]:
    """Translate individual parts of a compound word."""
    if not parts:
        return []

    parts_str = ", ".join(f'"{p}"' for p in parts)
    prompt = f"""Translate these word parts from {source_lang} to {target_lang}: {parts_str}

Return JSON with:
- translations: array of objects with "part" and "translation" for each word

Return ONLY valid JSON."""

    result = llm_call(prompt, model=SMART_MODEL)

    if isinstance(result, dict) and "translations" in result:
        return [(t.get("part", ""), t.get("translation", "")) for t in result["translations"]]

    # Fallback: translate each part individually
    return [(part, translate_simple(part, source_lang, target_lang)) for part in parts]

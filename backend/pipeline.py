import logging
import time
from dataclasses import dataclass

from analyzer import analyze_word
from breakdown import generate_breakdown
from translator import translate_word, translate_simple, generate_example, translate_compound_parts
from languages import get_language
from timing import start_timing_context, record_timing, log_timing_summary, TimingBlock

log = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    translation: str
    meaning: str | None = None
    breakdown: str | None = None
    example: dict | None = None  # {"source": str, "target": str}

    def to_dict(self) -> dict:
        result = {"translation": self.translation}
        if self.meaning:
            result["meaning"] = self.meaning
        if self.breakdown:
            result["breakdown"] = self.breakdown
        if self.example and self.example.get("source"):
            result["example"] = self.example
        return result


def try_split_compound(word: str, lang: str) -> list[str] | None:
    """Try to split a compound word using language-specific rules."""
    lang_module = get_language(lang)
    if not lang_module or not lang_module.should_split_compound(word):
        return None

    try:
        from compound_split import char_split
        # char_split.split_compound returns list of tuples (score, part1, part2, ...)
        results = char_split.split_compound(word)
        if results and len(results) > 0:
            best = results[0]
            if isinstance(best, tuple) and len(best) > 1:
                score = best[0]
                parts = list(best[1:])

                # Only trust high-confidence splits (positive score)
                if score < 0.5:
                    return None

                # Reject if first part is a prefix that shouldn't be split
                if lang_module.is_compound_prefix(parts[0]):
                    return None

                if len(parts) > 1:
                    # Clean linking elements from first part
                    parts[0] = lang_module.clean_compound_part(parts[0])
                    return parts
    except (ImportError, Exception) as e:
        log.warning(f"[COMPOUND] Split failed: {e}")

    return None


def translate_pipeline(
    text: str,
    context: str = "",
    source_lang: str = "auto",
    target_lang: str = "en",
    mode: str = "simple",
) -> TranslationResult:
    """
    Full translation pipeline.

    Args:
        text: Word to translate
        context: Surrounding sentence for context
        source_lang: Source language code or 'auto'
        target_lang: Target language code
        mode: 'simple' for quick translation, 'smart' for full analysis

    Returns:
        TranslationResult with translation and optional details
    """
    log.info(f"[PIPELINE] Starting translation: text='{text}', mode={mode}, target={target_lang}")
    if context:
        log.info(f"[PIPELINE] Context: '{context[:50]}...'" if len(context) > 50 else f"[PIPELINE] Context: '{context}'")

    start_timing_context()
    pipeline_start = time.perf_counter()

    # Simple mode - just translate
    if mode == "simple":
        log.info("[PIPELINE] Mode: simple - calling translate_simple()")
        with TimingBlock("translate_simple"):
            trans_result = translate_simple(text, source_lang, target_lang)
        log.info(f"[PIPELINE] Simple result: '{trans_result['translation']}'")
        log_timing_summary()
        return TranslationResult(translation=trans_result["translation"])

    # Smart mode - full pipeline
    log.info("[PIPELINE] Mode: smart - starting full pipeline")

    # Step 1: Analyze word
    log.info("[STEP 1] Analyzing word with spaCy...")
    with TimingBlock("Step 1: analyze_word"):
        analysis = analyze_word(text, context, source_lang)
    detected_lang = analysis.lang
    log.info(f"[STEP 1] Analysis result:")
    log.info(f"         - Language: {analysis.lang}")
    log.info(f"         - Lemma: {analysis.lemma}")
    log.info(f"         - POS: {analysis.pos}")
    log.info(f"         - Morph: {analysis.morph}")
    log.info(f"         - Word type: {analysis.word_type}")

    # Step 2: Translate with meaning
    log.info("[STEP 2] Translating word with LLM...")
    with TimingBlock("Step 2: translate_word"):
        trans_result = translate_word(text, detected_lang, target_lang, context)
    translation = trans_result["translation"]
    meaning = trans_result["meaning"]
    log.info(f"[STEP 2] Translation: '{translation}'")
    log.info(f"[STEP 2] Meaning: '{meaning}'")

    # Step 3: Generate breakdown if needed
    breakdown = None
    if analysis.word_type != "simple":
        log.info(f"[STEP 3] Generating breakdown for word_type='{analysis.word_type}'...")
        with TimingBlock("Step 3: breakdown"):
            # For compound nouns, try to split and translate parts
            compound_parts = None
            if analysis.word_type == "compound_noun":
                log.info("[STEP 3] Attempting compound split...")
                parts = try_split_compound(text, detected_lang)
                if parts:
                    log.info(f"[STEP 3] Compound parts: {parts}")
                    compound_parts = translate_compound_parts(parts, detected_lang, target_lang)
                    log.info(f"[STEP 3] Translated parts: {compound_parts}")
                else:
                    log.info("[STEP 3] No compound split found")

            # Get base form translation for breakdown
            base_translation = translation
            if analysis.lemma != text:
                log.info(f"[STEP 3] Translating lemma '{analysis.lemma}'...")
                base_result = translate_word(analysis.lemma, detected_lang, target_lang)
                base_translation = base_result["translation"]
                log.info(f"[STEP 3] Lemma translation: '{base_translation}'")

            breakdown = generate_breakdown(analysis, base_translation, compound_parts)
        log.info(f"[STEP 3] Breakdown: '{breakdown}'")
    else:
        log.info("[STEP 3] Skipping breakdown (word_type='simple')")

    # Step 4: Generate example (using same meaning as in context)
    log.info("[STEP 4] Generating example sentence with same meaning...")
    with TimingBlock("Step 4: generate_example"):
        example = generate_example(text, detected_lang, target_lang, meaning)
    log.info(f"[STEP 4] Example source: '{example.get('source', '')}'")
    log.info(f"[STEP 4] Example target: '{example.get('target', '')}'")

    total_ms = (time.perf_counter() - pipeline_start) * 1000
    record_timing("Total pipeline", total_ms)

    result = TranslationResult(
        translation=translation,
        meaning=meaning,
        breakdown=breakdown,
        example=example if example.get("source") else None,
    )
    log.info(f"[PIPELINE] Final result: {result.to_dict()}")

    log_timing_summary()
    return result

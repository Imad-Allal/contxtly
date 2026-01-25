import logging
import time
from dataclasses import dataclass

from analyzer import analyze_word
from breakdown import generate_breakdown
from translator import translate_smart, translate_simple
from languages import get_language
from timing import start_timing_context, record_timing, log_timing_summary, TimingBlock

log = logging.getLogger(__name__)


@dataclass
class TranslationResult:
    translation: str
    meaning: str | None = None
    breakdown: str | None = None
    context_translation: dict | None = None  # {"source": original context, "target": translated context}

    def to_dict(self) -> dict:
        result = {"translation": self.translation}
        if self.meaning:
            result["meaning"] = self.meaning
        if self.breakdown:
            result["breakdown"] = self.breakdown
        if self.context_translation and self.context_translation.get("source"):
            result["context_translation"] = self.context_translation
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

    # Try char_split first (free, local) for compound words
    is_compound = analysis.word_type in ("compound_noun", "compound_adjective")
    char_split_parts = None
    if is_compound:
        log.info("[STEP 1.5] Trying char_split for compound (free, local)...")
        char_split_parts = try_split_compound(text, detected_lang)
        if char_split_parts:
            log.info(f"[STEP 1.5] char_split succeeded: {char_split_parts}")
        else:
            log.info("[STEP 1.5] char_split failed, LLM will handle splitting")

    # Step 2: Smart translate (translation + meaning + base + example + compound in one call)
    log.info("[STEP 2] Smart translating with LLM (combined call)...")
    lemma_to_translate = analysis.lemma if analysis.lemma != text else None
    # Only ask LLM to split if char_split failed
    need_llm_compound_split = is_compound and not char_split_parts
    with TimingBlock("Step 2: translate_smart"):
        smart_result = translate_smart(
            text, detected_lang, target_lang, context, lemma_to_translate,
            is_compound=need_llm_compound_split,
            compound_parts_to_translate=char_split_parts,
        )
    translation = smart_result["translation"]
    meaning = smart_result["meaning"]
    base_translation = smart_result.get("base_translation", translation)
    context_translation_text = smart_result.get("context_translation")
    compound_parts = smart_result.get("compound_parts")
    log.info(f"[STEP 2] Translation: '{translation}'")
    log.info(f"[STEP 2] Meaning: '{meaning}'")
    log.info(f"[STEP 2] Base translation: '{base_translation}'")
    if context_translation_text:
        log.info(f"[STEP 2] Context translation: '{context_translation_text}'")
    if compound_parts:
        log.info(f"[STEP 2] Compound parts: {compound_parts}")

    # Step 3: Generate breakdown if needed
    breakdown = None
    if analysis.word_type != "simple":
        log.info(f"[STEP 3] Generating breakdown for word_type='{analysis.word_type}'...")
        with TimingBlock("Step 3: breakdown"):
            # Use base_translation from smart result (already fetched in Step 2)
            if not base_translation:
                base_translation = translation

            # compound_parts already available from Step 2
            breakdown = generate_breakdown(analysis, base_translation, compound_parts)
        log.info(f"[STEP 3] Breakdown: '{breakdown}'")
    else:
        log.info("[STEP 3] Skipping breakdown (word_type='simple')")

    total_ms = (time.perf_counter() - pipeline_start) * 1000
    record_timing("Total pipeline", total_ms)

    # Build context_translation as {source, target} format
    context_translation = None
    if context and context_translation_text:
        context_translation = {"source": context, "target": context_translation_text}

    result = TranslationResult(
        translation=translation,
        meaning=meaning,
        breakdown=breakdown,
        context_translation=context_translation,
    )
    log.info(f"[PIPELINE] Final result: {result.to_dict()}")

    log_timing_summary()
    return result

import logging
import time
from dataclasses import dataclass

from analyzer import analyze_word
from breakdown import generate_breakdown
from translator import translate_smart, translate_simple
from languages import get_language
from timing import start_timing_context, record_timing, log_timing_summary, TimingBlock
from cache import cache, CachedTranslation

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

    # Check cache - full hit (same word+context)
    cached = cache.get(text, context, detected_lang, target_lang)
    if cached:
        log.info(f"[CACHE] HIT for '{text}'")
        log_timing_summary()
        return TranslationResult(
            translation=cached.translation,
            meaning=cached.meaning,
            breakdown=cached.breakdown,
            context_translation=cached.context_translation,
        )

    # Check if context translation is cached (different word, same context)
    cached_context_translation = cache.get_context(context, detected_lang, target_lang) if context else None
    if cached_context_translation:
        log.info(f"[CACHE] Context HIT - reusing cached context translation")

    log.info(f"[STEP 1] Analysis result:")
    log.info(f"         - Language: {analysis.lang}")
    log.info(f"         - Lemma: {analysis.lemma}")
    log.info(f"         - POS: {analysis.pos}")
    log.info(f"         - Morph: {analysis.morph}")
    log.info(f"         - Word type: {analysis.word_type}")
    if analysis.separable_verb:
        log.info(f"         - Separable verb: {analysis.separable_verb}")

    # Use separable verb if detected (e.g., "ziehe" → "anziehen")
    word_to_translate = analysis.separable_verb or text

    # Try to split compound words (NOUN and PROPN - proper nouns like "Bundesverfassungsgericht")
    compound_parts = None
    lang_module = get_language(detected_lang)
    if analysis.pos in ("NOUN", "PROPN") and lang_module:
        parts = lang_module.split_compound(text)
        if parts and len(parts) > 1:
            log.info(f"[STEP 1.5] Compound split: {text} → {parts}")
            compound_parts = parts

    # Step 2: Smart translate (translation + meaning + base + context translation in one call)
    log.info(f"[STEP 2] Smart translating with LLM: '{word_to_translate}'...")
    # For separable verbs, we already have the infinitive - no need to translate lemma separately
    # For regular verbs, translate lemma if different from conjugated form
    lemma_to_translate = None if analysis.separable_verb else (analysis.lemma if analysis.lemma != text else None)
    with TimingBlock("Step 2: translate_smart"):
        smart_result = translate_smart(
            word_to_translate, detected_lang, target_lang, context, lemma_to_translate,
            skip_context_translation=cached_context_translation is not None,
            compound_parts=compound_parts,
        )
    translation = smart_result["translation"]
    meaning = smart_result["meaning"]
    base_translation = smart_result.get("base_translation", translation)
    context_translation_text = smart_result.get("context_translation")
    translated_parts = smart_result.get("compound_parts")
    log.info(f"[STEP 2] Translation: '{translation}'")
    log.info(f"[STEP 2] Meaning: '{meaning}'")
    log.info(f"[STEP 2] Base translation: '{base_translation}'")
    if context_translation_text:
        log.info(f"[STEP 2] Context translation: '{context_translation_text}'")
    if translated_parts:
        log.info(f"[STEP 2] Compound parts: {translated_parts}")

    # Step 3: Generate breakdown if needed
    breakdown = None
    if analysis.word_type != "simple" or translated_parts:
        log.info(f"[STEP 3] Generating breakdown for word_type='{analysis.word_type}'...")
        with TimingBlock("Step 3: breakdown"):
            if not base_translation:
                base_translation = translation

            breakdown = generate_breakdown(analysis, base_translation, translated_parts)
        log.info(f"[STEP 3] Breakdown: '{breakdown}'")
    else:
        log.info("[STEP 3] Skipping breakdown (word_type='simple')")

    total_ms = (time.perf_counter() - pipeline_start) * 1000
    record_timing("Total pipeline", total_ms)

    # Build context_translation (use cached if available, otherwise from LLM)
    context_translation = None
    if context:
        ctx_target = cached_context_translation or context_translation_text
        if ctx_target:
            context_translation = {"source": context, "target": ctx_target}

    # Store in cache
    cache.set(
        text, context, detected_lang, target_lang,
        CachedTranslation(
            translation=translation,
            meaning=meaning,
            breakdown=breakdown,
            context_translation=context_translation,
        ),
    )

    result = TranslationResult(
        translation=translation,
        meaning=meaning,
        breakdown=breakdown,
        context_translation=context_translation,
    )
    log.info(f"[PIPELINE] Final result: {result.to_dict()}")

    log_timing_summary()
    return result

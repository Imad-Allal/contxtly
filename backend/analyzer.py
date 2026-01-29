import logging
import time
from dataclasses import dataclass
from langdetect import detect, LangDetectException
import spacy

from languages import get_language, get_spacy_models
from timing import record_timing

log = logging.getLogger(__name__)

_models: dict[str, spacy.Language] = {}


@dataclass
class WordAnalysis:
    text: str
    lemma: str
    pos: str
    morph: dict[str, str]
    lang: str
    word_type: str  # simple, conjugated_verb, compound_noun, plural_noun
    compound_tense: str | None = None  # For compound tenses like Perfekt, Futur I, etc.
    separable_verb: str | None = None  # Reconstructed infinitive for separable verbs (e.g., "anziehen")


def detect_language(text: str) -> str:
    """Detect language of text. Returns ISO 639-1 code (e.g., 'de', 'en')."""
    try:
        lang = detect(text)
        log.debug(f"[LANG] Detected language: {lang} for text: '{text[:30]}...'")
        return lang
    except LangDetectException as e:
        log.warning(f"[LANG] Detection failed: {e}, defaulting to 'en'")
        return "en"


def get_model(lang: str) -> spacy.Language | None:
    """Get spaCy model for language, loading lazily."""
    spacy_models = get_spacy_models()
    if lang not in spacy_models:
        log.warning(f"[SPACY] No model available for language: {lang}")
        return None

    if lang not in _models:
        try:
            log.info(f"[SPACY] Loading model: {spacy_models[lang]}")
            _models[lang] = spacy.load(spacy_models[lang])
            log.info(f"[SPACY] Model loaded successfully")
        except OSError as e:
            log.error(f"[SPACY] Failed to load model: {e}")
            return None

    return _models[lang]


def preload_models() -> None:
    """Preload all spaCy models and warm up language detection at startup."""
    log.info("[PRELOAD] Starting model preload...")

    # Warm up langdetect (loads its models on first call)
    try:
        detect("hello world")
        log.info("[PRELOAD] Language detection warmed up")
    except LangDetectException:
        pass

    # Preload all spaCy models
    spacy_models = get_spacy_models()
    for lang, model_name in spacy_models.items():
        if lang not in _models:
            try:
                log.info(f"[PRELOAD] Loading spaCy model: {model_name}")
                _models[lang] = spacy.load(model_name)
            except OSError as e:
                log.warning(f"[PRELOAD] Failed to load {model_name}: {e}")

    # Warm up compound_split (loads data files on first use)
    try:
        from compound_split import char_split
        char_split.split_compound("Handschuh")  # Warm up with a sample word
        log.info("[PRELOAD] compound_split warmed up")
    except ImportError:
        log.info("[PRELOAD] compound_split not available")
    except Exception as e:
        log.warning(f"[PRELOAD] compound_split warmup failed: {e}")

    log.info(f"[PRELOAD] Completed. Loaded {len(_models)} spaCy models")


def parse_morphology(morph) -> dict[str, str]:
    """Parse spaCy morphology into a dict."""
    result = {}
    for item in morph:
        if "=" in item:
            key, val = item.split("=", 1)
            result[key] = val
    return result


def classify_word_type(token, lang: str, has_compound_tense: bool = False) -> str:
    """Classify word type based on POS and morphology."""
    pos = token.pos_
    morph = parse_morphology(token.morph)

    # Verbs with tense/mood markers
    if pos == "VERB" and any(k in morph for k in ["Tense", "Mood", "VerbForm"]):
        # Include infinitives if they're part of a compound tense (e.g., "wird sprechen")
        if morph.get("VerbForm") != "Inf" or has_compound_tense:
            return "conjugated_verb"

    # Nouns - use language module for classification
    if pos == "NOUN":
        lang_module = get_language(lang)
        if lang_module:
            return lang_module.classify_noun(token, morph)
        # Fallback for unsupported languages
        if morph.get("Number") == "Plur":
            return "plural_noun"

    # Adjectives - check for compound adjectives
    if pos == "ADJ":
        lang_module = get_language(lang)
        if lang_module:
            return lang_module.classify_adjective(token, morph)

    return "simple"


def analyze_word(text: str, context: str = "", source_lang: str = "auto") -> WordAnalysis:
    """Analyze a word using spaCy."""
    start = time.perf_counter()

    # Detect language if auto
    if source_lang == "auto":
        # Use context for better detection if available
        lang = detect_language(context if context else text)
        record_timing("language detection", (time.perf_counter() - start) * 1000)
    else:
        lang = source_lang

    spacy_start = time.perf_counter()
    nlp = get_model(lang)
    record_timing("spaCy get_model", (time.perf_counter() - spacy_start) * 1000)

    if nlp is None:
        # Fallback if no model available
        return WordAnalysis(
            text=text,
            lemma=text.lower(),
            pos="UNKNOWN",
            morph={},
            lang=lang,
            word_type="simple",
        )

    # Analyze the word (use context if available for better accuracy)
    if context:
        doc = nlp(context)
        # Find our word in the context
        token = None
        text_lower = text.lower()
        for t in doc:
            if t.text.lower() == text_lower:
                token = t
                break
        if token is None:
            # Word not found in context, analyze alone
            doc = nlp(text)
            token = doc[0] if doc else None
    else:
        doc = nlp(text)
        token = doc[0] if doc else None

    if token is None:
        return WordAnalysis(
            text=text,
            lemma=text.lower(),
            pos="UNKNOWN",
            morph={},
            lang=lang,
            word_type="simple",
        )

    morph = parse_morphology(token.morph)

    # Detect compound tenses (e.g., Perfekt, Futur I) from context
    compound_tense = None
    lang_module = get_language(lang)
    if lang_module and hasattr(lang_module, "detect_compound_tense") and context:
        compound_tense = lang_module.detect_compound_tense(text, doc)

    # Detect separable verbs (e.g., "ziehe" in "Ich ziehe mich an" → "anziehen")
    separable_verb = None
    if lang_module and hasattr(lang_module, "detect_separable_verb") and context:
        separable_verb = lang_module.detect_separable_verb(text, doc)

    # Classify word type (compound tense affects classification)
    word_type = classify_word_type(token, lang, has_compound_tense=bool(compound_tense))

    return WordAnalysis(
        text=token.text,
        lemma=token.lemma_,
        pos=token.pos_,
        morph=morph,
        lang=lang,
        word_type=word_type,
        compound_tense=compound_tense,
        separable_verb=separable_verb,
    )

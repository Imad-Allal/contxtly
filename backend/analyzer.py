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
    )

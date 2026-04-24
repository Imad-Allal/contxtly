import logging
import time
from dataclasses import dataclass
from langdetect import detect, LangDetectException
import spacy
import simplemma

from languages import get_language, get_spacy_models
from languages.base import LanguageAnalysis
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
    word_type: str  # simple, conjugated_verb, plural_noun, adjective, separable_prefix, collocation_verb, collocation_prep, fixed_expression
    lang_analysis: LanguageAnalysis | None = None


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

    log.info(f"[PRELOAD] Completed. Loaded {len(_models)} spaCy models")


def parse_morphology(morph) -> dict[str, str]:
    """Parse spaCy morphology into a dict."""
    result = {}
    for item in morph:
        if "=" in item:
            key, val = item.split("=", 1)
            result[key] = val
    return result


def fix_german_verb_morph(token, morph: dict, doc) -> dict:
    """Fix verb Person/Number from the subject pronoun's spaCy morph.

    Only applies when Person or Number is missing — happens when spaCy misclassified
    the verb as NOUN and we corrected effective_pos to VERB. spaCy correctly
    morphologizes pronouns even in de_core_news_lg, so we read directly from them.
    """
    text = token.text.lower()
    if text.endswith("est") and len(text) > 3 and text[-4] not in "aeiouäöüy" and morph.get("Person") != "2":
        return {**morph, "Person": "2", "Number": "Sing", "Tense": "Pres", "VerbForm": "Fin", "Mood": "Ind"}

    if "Person" in morph and "Number" in morph:
        return morph

    for t in doc:
        if t.pos_ != "PRON":
            continue
        pron_morph = parse_morphology(t.morph)
        person = pron_morph.get("Person")
        number = pron_morph.get("Number")
        if person and number:
            return {**morph, "Person": person, "Number": number, "Tense": "Pres", "VerbForm": "Fin", "Mood": "Ind"}

    return morph


def classify_word_type(token, lang: str, effective_pos: str | None = None, corrected_morph: dict | None = None) -> str:
    """Classify word type based on POS and morphology."""
    pos = effective_pos or token.pos_
    morph = corrected_morph if corrected_morph is not None else parse_morphology(token.morph)

    # Verbs with tense/mood markers (excluding bare infinitives)
    if pos == "VERB" and any(k in morph for k in ["Tense", "Mood", "VerbForm"]):
        if morph.get("VerbForm") != "Inf":
            return "conjugated_verb"

    if pos == "VERB":
        return "verb"

    # Nouns - use language module for classification
    if pos == "NOUN":
        lang_module = get_language(lang)
        if lang_module:
            return lang_module.classify_noun(token, morph)
        # Fallback for unsupported languages
        if morph.get("Number") == "Plur":
            return "plural_noun"
        return "noun"

    if pos == "ADJ":
        return "adjective"

    return "simple"


def analyze_word(text: str, context: str = "", source_lang: str = "auto", text_offset: int | None = None) -> WordAnalysis:
    """Analyze a word using spaCy.

    Args:
        text: The word to analyze
        context: Surrounding sentence for context
        source_lang: Source language code or 'auto'
        text_offset: Character offset of the word within the context string.
                     Used to disambiguate when the same word appears multiple times.
    """
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

        if text_offset is not None:
            # Use character offset to find the exact token (handles duplicate words)
            for t in doc:
                if t.idx == text_offset and t.text.lower() == text_lower:
                    token = t
                    break

        if token is None:
            # Fallback: find by text match (first occurrence)
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

    # Correct spaCy POS for German: if tagged NOUN but the token is lowercase
    # and simplemma gives a verb lemma, it's a verb misclassified by de_core_news_lg
    effective_pos = token.pos_
    if lang == "de" and token.pos_ == "NOUN" and token.text[0].islower():
        sm_lemma = simplemma.lemmatize(token.text.lower(), lang="de")
        if sm_lemma and sm_lemma != token.text.lower() and not sm_lemma[0].isupper():
            effective_pos = "VERB"
    if lang == "de" and token.tag_ == "ADJD" and token.dep_ == "oc" and token.head.lemma_ in ("haben", "sein"):
        sm_lemma = simplemma.lemmatize(token.text.lower(), lang="de")
        if sm_lemma and sm_lemma != token.text.lower():
            effective_pos = "VERB"

    morph = parse_morphology(token.morph)
    if lang == "de" and doc is not None:
        morph = fix_german_verb_morph(token, morph, doc)

    # Run language-specific analysis (separable verbs, collocations, compound tenses, etc.)
    lang_module = get_language(lang)
    lang_analysis = None
    if lang_module and context:
        lang_analysis = lang_module.analyze(text, token, doc, morph, nlp)

    # word_type: language analysis overrides generic POS-based classification
    word_type = (lang_analysis.word_type if lang_analysis and lang_analysis.word_type
                 else classify_word_type(token, lang, effective_pos, morph))

    # Use simplemma for verbs — more reliable for irregular forms (e.g. schloss → schließen)
    if lang == "de" and effective_pos == "VERB":
        lemma = simplemma.lemmatize(token.text, lang=lang) or token.lemma_
    elif lang == "de" and effective_pos == "NOUN" and "ß" in token.lemma_:
        # Fix old German spelling in noun lemmas (e.g. Fluß → Fluss)
        lemma = simplemma.lemmatize(token.text, lang=lang) or token.lemma_
    else:
        lemma = token.lemma_

    return WordAnalysis(
        text=token.text,
        lemma=lemma,
        pos=effective_pos,
        morph=morph,
        lang=lang,
        word_type=word_type,
        lang_analysis=lang_analysis,
    )

"""German verb detection: separable verbs and compound tenses."""

import spacy
from models import TokenRef


def detect_separable_verb(word: str, doc: spacy.tokens.Doc) -> tuple[str, TokenRef] | None:
    """
    Detect if a verb is part of a separable verb construction.

    Example: "Ich ziehe mich an" → "ziehe" is part of "anziehen"

    Args:
        word: The selected word (e.g., "ziehe")
        doc: spaCy Doc of the context

    Returns:
        Tuple of (infinitive, prefix_ref) or None if not separable
    """
    target_token = None
    for token in doc:
        if token.text.lower() == word.lower():
            target_token = token
            break

    if not target_token or target_token.pos_ != "VERB":
        return None

    lemma = target_token.lemma_

    for token in doc:
        if token.head == target_token:
            if token.tag_ == "PTKVZ" or token.dep_ == "svp":
                return (token.text.lower() + lemma, TokenRef(token.text, token.idx))

    return None


def detect_separable_verb_from_prefix(word: str, doc: spacy.tokens.Doc) -> tuple[str, str, dict, int] | None:
    """
    Detect full separable verb when user selects the prefix/particle.

    Example: "Er legte das Buch nieder" → "nieder" → "niederlegen"

    Args:
        word: The selected word (e.g., "nieder")
        doc: spaCy Doc of the context

    Returns:
        Tuple of (infinitive, verb_text, verb_morph, verb_offset) or None if not a separable verb particle
    """
    target_token = None
    for token in doc:
        if token.text.lower() == word.lower():
            target_token = token
            break

    if not target_token:
        return None

    # Check if this token is a separable verb particle (PTKVZ tag or svp dependency)
    if target_token.tag_ != "PTKVZ" and target_token.dep_ != "svp":
        return None

    # The head of the particle is the verb stem
    verb_token = target_token.head
    if verb_token.pos_ != "VERB":
        return None

    # Parse verb morphology
    verb_morph = {}
    for item in verb_token.morph:
        if "=" in item:
            key, val = item.split("=", 1)
            verb_morph[key] = val

    # Return infinitive, verb text, verb morphology, and verb character offset
    infinitive = word.lower() + verb_token.lemma_
    return (infinitive, verb_token.text, verb_morph, verb_token.idx)


# German compound tense patterns
GERMAN_COMPOUND_TENSES = {
    ("haben", "Pres", "Part"): "Perfekt (present perfect)",
    ("sein", "Pres", "Part"): "Perfekt (present perfect)",
    ("haben", "Past", "Part"): "Plusquamperfekt (past perfect)",
    ("sein", "Past", "Part"): "Plusquamperfekt (past perfect)",
    ("werden", "Pres", "Inf"): "Futur I (future)",
    ("werden", "Pres", "Part"): "Futur II (future perfect)",
    ("werden", "Sub", "Inf"): "Konjunktiv II (subjunctive)",
}

GERMAN_AUXILIARIES = {"haben", "sein", "werden"}


def detect_compound_tense(target_word: str, doc: spacy.tokens.Doc) -> str | None:
    """Detect German compound tenses by analyzing auxiliary + main verb patterns."""
    main_verb = None
    aux_verb = None

    for token in doc:
        if token.text.lower() == target_word.lower():
            main_verb = token
        if token.lemma_ in GERMAN_AUXILIARIES:
            aux_verb = token

    if not (aux_verb and main_verb):
        return None

    aux_morph = dict(aux_verb.morph.to_dict())
    main_morph = dict(main_verb.morph.to_dict())

    aux_lemma = aux_verb.lemma_
    aux_tense = aux_morph.get("Tense") or aux_morph.get("Mood", "")
    main_form = main_morph.get("VerbForm", "")

    key = (aux_lemma, aux_tense, main_form)
    return GERMAN_COMPOUND_TENSES.get(key)

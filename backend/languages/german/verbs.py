"""German verb detection: separable verbs and compound tenses."""

import simplemma
import spacy
from models import TokenRef

# Known separable verb prefixes - used as fallback when spaCy misses PTKVZ tagging
SEPARABLE_PREFIXES = frozenset({
    "ab", "an", "auf", "aus", "bei", "ein", "fest", "her", "hin", "los",
    "mit", "nach", "vor", "weg", "zu", "zurück", "zusammen", "weiter",
    "da", "dar", "empor", "fort", "heim", "nieder", "um", "vorbei",
})


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

    if not target_token:
        return None

    for token in doc:
        if token.head != target_token:
            continue
        is_particle = token.tag_ == "PTKVZ" or token.dep_ == "svp"
        is_known_prefix = (token.text.lower() in SEPARABLE_PREFIXES
                           and token.pos_ not in ("DET", "PRON", "NOUN")
                           and token.dep_ not in ("nk", "mo", "sb", "og", "da", "oa"))
        if is_particle or is_known_prefix:
            # Lemmatize the verb using simplemma (more reliable than spaCy for irregular verbs)
            verb_lemma = simplemma.lemmatize(target_token.text, lang="de")
            infinitive = token.text.lower() + verb_lemma
            return (infinitive, TokenRef(token.text, token.idx))

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

    # Check if this token is a separable verb particle (PTKVZ tag, svp dependency, or known prefix)
    is_particle = target_token.tag_ == "PTKVZ" or target_token.dep_ == "svp"
    is_known_prefix = (target_token.text.lower() in SEPARABLE_PREFIXES
                       and target_token.pos_ not in ("DET", "PRON", "NOUN")
                       and target_token.dep_ not in ("nk", "mo", "sb", "og", "da", "oa"))
    if not is_particle and not is_known_prefix:
        return None

    # The head of the particle is the verb stem
    # Trust PTKVZ tagging even if verb is misclassified (e.g. imperatives tagged as NOUN)
    verb_token = target_token.head
    if verb_token.pos_ not in ("VERB", "NOUN", "AUX"):
        return None

    # Parse verb morphology
    verb_morph = {}
    for item in verb_token.morph:
        if "=" in item:
            key, val = item.split("=", 1)
            verb_morph[key] = val

    # Lemmatize the verb using simplemma (more reliable than spaCy for irregular verbs)
    verb_lemma = simplemma.lemmatize(verb_token.text, lang="de")
    infinitive = word.lower() + verb_lemma
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


def _are_syntactically_related(aux, main_verb) -> bool:
    """Check if auxiliary and main verb are in the same verb group (dependency-linked)."""
    # Direct relationship: one is the head of the other
    if main_verb.head == aux or aux.head == main_verb:
        return True
    # Same head (siblings in the dependency tree)
    if main_verb.head == aux.head:
        return True
    # Auxiliary is ancestor of main verb (within 2 hops)
    head = main_verb.head
    for _ in range(2):
        if head == aux:
            return True
        head = head.head
    return False


def detect_compound_tense(target_word: str, doc: spacy.tokens.Doc) -> str | None:
    """Detect German compound tenses by analyzing auxiliary + main verb patterns."""
    main_verb = None
    for token in doc:
        if token.text.lower() == target_word.lower():
            main_verb = token
            break

    if not main_verb:
        return None

    # Find the closest syntactically-related auxiliary
    best_aux = None
    for token in doc:
        if token.lemma_ in GERMAN_AUXILIARIES and _are_syntactically_related(token, main_verb):
            best_aux = token
            break

    if not best_aux:
        return None

    aux_morph = dict(best_aux.morph.to_dict())
    main_morph = dict(main_verb.morph.to_dict())

    aux_lemma = best_aux.lemma_
    aux_tense = aux_morph.get("Tense") or aux_morph.get("Mood", "")
    main_form = main_morph.get("VerbForm", "")

    key = (aux_lemma, aux_tense, main_form)
    return GERMAN_COMPOUND_TENSES.get(key)

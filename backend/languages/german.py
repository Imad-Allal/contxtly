"""German language configuration."""

import logging
import spacy
from languages.base import LanguageConfig, LanguageModule

log = logging.getLogger(__name__)

# Derivational suffixes - words ending in these are derived from verbs/adjectives
DERIVATIONAL_SUFFIXES = ("ung", "heit", "keit", "schaft", "nis", "tum", "ling")

# Verb prefixes - when combined with derivational suffix = derived word, not compound
VERB_PREFIXES = frozenset({
    # Separable prefixes
    "ab", "an", "auf", "aus", "bei", "ein", "fest", "her", "hin", "los",
    "mit", "nach", "vor", "weg", "zu", "zurück", "zusammen", "weiter",
    "da", "dar", "empor", "fort", "heim", "nieder", "um", "vorbei",
    # Inseparable prefixes
    "be", "ent", "emp", "er", "ge", "miss", "ver", "zer",
})

# Linking elements in compounds (Fugenelement)
LINKING_PATTERNS = [
    ("ungs", "ung"),        # Verhandlungs -> Verhandlung
    ("ions", "ion"),        # Kommunikations -> Kommunikation
    ("täts", "tät"),        # Universitäts -> Universität
    ("heits", "heit"),      # Freiheits -> Freiheit
    ("keits", "keit"),      # Möglichkeits -> Möglichkeit
    ("schafts", "schaft"),  # Gesellschafts -> Gesellschaft
    ("eits", "eit"),        # Arbeits -> Arbeit
    ("ens", "en"),          # Studentens -> Studenten
    ("ns", "n"),            # Herzens -> Herzen
    ("es", ""),             # Kindes -> Kind
]


def _is_derived_word(word: str, parts: list[str]) -> bool:
    """Check if a word is derived (not a true compound) based on split parts."""
    if len(parts) != 2:
        return False

    first_part = parts[0].lower()
    word_lower = word.lower()

    # If ends with derivational suffix AND first part is a verb prefix → derived
    if any(word_lower.endswith(suffix) for suffix in DERIVATIONAL_SUFFIXES):
        if first_part in VERB_PREFIXES:
            return True

    return False


def _clean_compound_part(part: str) -> str:
    """Remove linking elements from compound parts (Fugenelement)."""
    part_lower = part.lower()
    for link, base in LINKING_PATTERNS:
        if part_lower.endswith(link) and len(part) > len(link) + 2:
            return part[:-len(link)] + base
    return part


def _split_once(word: str, min_score: float = 0.4) -> tuple[str, str] | None:
    """
    Split a word into exactly two parts using CharSplit.

    Args:
        word: The word to split
        min_score: Minimum confidence score

    Returns:
        Tuple of (left_part, right_part) or None if no good split
    """
    try:
        from compound_split import char_split
    except ImportError:
        return None

    results = char_split.split_compound(word)
    if not results:
        return None

    best = results[0]
    if not isinstance(best, tuple) or len(best) < 3:
        return None

    score = best[0]
    if score < min_score:
        return None

    return (best[1], best[2])


def split_compound(word: str, _depth: int = 0) -> list[str] | None:
    """
    Split a German compound word into its parts recursively.

    Uses CharSplit for splitting. Recursively splits parts that are
    long enough to handle multi-part compounds like "Krankenversicherungssystem".

    Args:
        word: The word to split (e.g., "Krankenhaus")
        _depth: Internal recursion depth counter

    Returns:
        List of parts or None if not a compound
    """
    # Prevent infinite recursion
    if _depth > 2:
        return None

    # Minimum word length to attempt splitting
    if len(word) < 6:
        return None

    # Use lower threshold for very long words (they tend to have lower CharSplit scores)
    if len(word) >= 18:
        min_score = -1.0  # Very long compounds
    elif _depth > 0:
        min_score = 0.5   # Stricter for recursive splits
    else:
        min_score = 0.4   # Normal compounds

    # Try to split the word
    split = _split_once(word, min_score)
    if not split:
        return None

    left, right = split

    # Validate: both parts should be reasonable length (min 3 chars)
    if len(left) < 3 or len(right) < 3:
        return None

    # Check if it's a derived word (Ausbildung, not Aus + Bildung)
    if _is_derived_word(word, [left, right]):
        return None

    # Clean linking elements from left part
    left = _clean_compound_part(left)

    # Recursively split the left part if it's long enough (likely another compound)
    # Only recurse if the part is substantial (>= 10 chars suggests it might be compound)
    result = []
    if len(left) >= 10:
        left_parts = split_compound(left, _depth + 1)
        if left_parts:
            result.extend(left_parts)
        else:
            result.append(left)
    else:
        result.append(left)

    result.append(right)

    return result if len(result) > 1 else None


def detect_separable_verb(word: str, doc: spacy.tokens.Doc) -> str | None:
    """
    Detect if a verb is part of a separable verb construction.

    Example: "Ich ziehe mich an" → "ziehe" is part of "anziehen"

    Args:
        word: The selected word (e.g., "ziehe")
        doc: spaCy Doc of the context

    Returns:
        The full infinitive (e.g., "anziehen") or None if not separable
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
                return token.text.lower() + lemma

    return None


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


class German(LanguageModule):
    """German language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="de",
            name="German",
            spacy_model="de_core_news_sm",
        )

    def detect_compound_tense(self, target_word: str, doc: spacy.tokens.Doc) -> str | None:
        """Detect German compound tenses from sentence context."""
        return detect_compound_tense(target_word, doc)

    def detect_separable_verb(self, word: str, doc: spacy.tokens.Doc) -> str | None:
        """Detect and reconstruct separable verbs from context."""
        return detect_separable_verb(word, doc)

    def split_compound(self, word: str) -> list[str] | None:
        """Split a compound word into parts."""
        return split_compound(word)

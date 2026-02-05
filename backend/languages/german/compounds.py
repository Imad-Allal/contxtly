"""German compound word splitting."""

# Derivational suffixes - words ending in these are derived from verbs/adjectives
DERIVATIONAL_SUFFIXES = ("ung", "heit", "keit", "schaft", "nis", "tum", "ling", "atz")

# Verb stems that form nouns when combined with prefixes (without suffix)
# e.g., aus+fallen -> Ausfall, ein+greifen -> Eingriff
VERB_STEM_NOUNS = frozenset({
    "fall", "gang", "griff", "zug", "schlag", "bruch", "schnitt", "schluss",
    "tritt", "wurf", "ruf", "lauf", "stoß", "druck", "blick", "sprung",
})

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

    # Nominalized infinitives: prefix + verb infinitive ending in "en"
    # e.g., "Vorhaben" (vor + haben), "Einkommen" (ein + kommen)
    # These are NOT compounds but nominalized verbs
    # Check: second part must also end in "en" (the verb infinitive part)
    # This distinguishes "Vorhaben" (vor+haben) from "Vorgarten" (vor+Garten)
    second_part = parts[1].lower()
    if word_lower.endswith("en") and first_part in VERB_PREFIXES and second_part.endswith("en"):
        return True

    # Verb stem nouns: prefix + verb stem (no suffix)
    # e.g., "Ausfall" (aus + fallen -> fall), "Eingriff" (ein + greifen -> griff)
    if first_part in VERB_PREFIXES and second_part in VERB_STEM_NOUNS:
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

    # Use lower threshold for long words (they tend to have lower CharSplit scores)
    if len(word) >= 15:
        min_score = -1.0  # Long compounds
    elif len(word) >= 10:
        min_score = 0.0   # Medium compounds
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

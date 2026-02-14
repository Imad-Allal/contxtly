"""German compound word splitting."""

import simplemma

# Derivational suffixes - words ending in these are derived from verbs/adjectives
DERIVATIONAL_SUFFIXES = ("ung", "heit", "keit", "schaft", "nis", "tum", "ling", "atz")

# Verb stems that form nouns when combined with prefixes (without suffix)
# e.g., aus+fallen -> Ausfall, ein+greifen -> Eingriff
VERB_STEM_NOUNS = frozenset({
    "fall", "gang", "griff", "zug", "schlag", "bruch", "schnitt", "schluss",
    "tritt", "wurf", "ruf", "lauf", "stoß", "druck", "blick", "sprung",
    "schied", "halt", "stand", "satz", "trieb", "schlug", "stieg", "schnitt",
})

# Verb prefixes - when combined with derivational suffix = derived word, not compound
VERB_PREFIXES = frozenset({
    # Separable prefixes
    "ab", "an", "auf", "aus", "bei", "ein", "fest", "her", "hin", "los",
    "mit", "nach", "vor", "weg", "zu", "zurück", "zusammen", "weiter",
    "da", "dar", "empor", "fort", "heim", "nieder", "um", "vorbei",
    # Inseparable prefixes
    "be", "ent", "emp", "er", "ge", "miss", "ver", "zer",
    # Dual prefixes (separable or inseparable depending on the verb)
    "unter", "über", "durch", "wider", "hinter", "wieder",
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

# Fugenlaute (linking sounds) - the "s" is the most common
# Used to prefer splits at Fugenlaut boundaries when scores are close
FUGENLAUTE = ("s", "n", "en", "er", "es", "ens", "ns")


def _is_derived_word(word: str, parts: list[str]) -> bool:
    """Check if a word is derived (not a true compound) based on split parts."""
    if len(parts) != 2:
        return False

    first_part = parts[0].lower()
    second_part = parts[1].lower()
    word_lower = word.lower()

    # If the right part IS a derivational suffix → derived, not compound
    # e.g., "Gesellschaft" → "Gesell" + "Schaft" — "-schaft" is a suffix
    if second_part in DERIVATIONAL_SUFFIXES:
        return True

    # If ends with derivational suffix AND first part is a verb prefix → derived
    if any(word_lower.endswith(suffix) for suffix in DERIVATIONAL_SUFFIXES):
        if first_part in VERB_PREFIXES:
            return True

    # Nominalized infinitives: prefix + verb infinitive ending in "en"
    # e.g., "Vorhaben" (vor + haben), "Einkommen" (ein + kommen)
    # These are NOT compounds but nominalized verbs
    # Check: second part must also end in "en" (the verb infinitive part)
    # This distinguishes "Vorhaben" (vor+haben) from "Vorgarten" (vor+Garten)
    if word_lower.endswith("en") and first_part in VERB_PREFIXES and second_part.endswith("en"):
        return True

    # Verb stem nouns: prefix + verb stem (no suffix)
    # e.g., "Ausfall" (aus + fallen -> fall), "Eingriff" (ein + greifen -> griff)
    if first_part in VERB_PREFIXES and second_part in VERB_STEM_NOUNS:
        return True

    return False


def _is_fugen_s(word: str) -> bool:
    """Check if trailing 's' in a word is a Fugen-s (linking sound), not part of the stem."""
    if len(word) < 5 or word[-1].lower() != "s" or word[-2:].lower() == "ss":
        return False
    stripped = word[:-1]
    if len(stripped) < 4:
        return False
    lemma = simplemma.lemmatize(word, lang="de")
    if lemma.lower() != word.lower():
        # Simplemma recognizes this as inflected → the 's' is a Fugenlaut
        return True
    # Fallback: simplemma returned word unchanged — could be unknown linking form
    # If the word itself is NOT known but the stripped form IS, it's likely Fugen-s
    # e.g., "Geburts" (unknown) → "Geburt" (known)
    if not simplemma.is_known(word, lang="de") and simplemma.is_known(stripped, lang="de"):
        return True
    return False


def _has_fugenlaut(left: str) -> bool:
    """Check if a compound left part ends with a Fugenlaut (linking sound)."""
    left_lower = left.lower()
    # Check structured linking patterns first (more specific)
    for link, base in LINKING_PATTERNS:
        if left_lower.endswith(link) and len(left) > len(link) + 2:
            return True
    # Check bare Fugen-s using word-level validation
    return _is_fugen_s(left)


def _clean_compound_part(part: str) -> str:
    """Remove linking elements from compound parts (Fugenelement)."""
    part_lower = part.lower()
    # Try structured linking patterns first (more specific, e.g., "ungs"→"ung", "es"→"")
    pattern_result = None
    for link, base in LINKING_PATTERNS:
        if part_lower.endswith(link) and len(part) > len(link) + 2:
            pattern_result = part[:-len(link)] + base
            break
    # Try bare Fugen-s (e.g., "Liebes"→"Liebe", "Einkaufs"→"Einkauf")
    fugen_s_result = part[:-1] if _is_fugen_s(part) else None
    if pattern_result and fugen_s_result:
        lemma = simplemma.lemmatize(fugen_s_result, lang="de")
        if lemma.lower() == pattern_result.lower():
            return pattern_result  # Pattern result matches the true lemma
        return fugen_s_result
    return fugen_s_result or pattern_result or part


# Present participle endings (inflected forms of -end)
PARTICIPLE_ENDINGS = ("end", "ende", "enden", "ender", "endem", "endes")


def _split_once(word: str, min_score: float = 0.4, prefer_participle: bool = False) -> tuple[str, str] | None:
    """
    Split a word into exactly two parts using CharSplit.

    Args:
        word: The word to split
        min_score: Minimum confidence score
        prefer_participle: If True, prefer splits where right part is a valid participle

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

    # Filter to valid results above minimum score, rejecting function-word parts
    _function_words = frozenset({
        "aus", "ein", "auf", "vor", "mit", "bei", "nach", "von",
        "für", "über", "unter", "bis", "durch", "ohne", "gegen",
        "der", "die", "das", "den", "dem", "des",
        "und", "oder", "aber", "als", "wie", "wenn", "weil",
    })
    valid_results = []
    for r in results:
        if not isinstance(r, tuple) or len(r) < 3:
            continue
        if r[0] < min_score:
            continue
        # Reject splits where either part is a short function word
        if r[1].lower() in _function_words or r[2].lower() in _function_words:
            continue
        valid_results.append(r)

    if not valid_results:
        return None

    # If looking for participle split, prefer splits where right part is a valid participle
    # (ends in -end/-ende/etc. and has a verb stem of at least 4 chars)
    if prefer_participle:
        for r in valid_results:
            right_lower = r[2].lower()
            for ending in PARTICIPLE_ENDINGS:
                if right_lower.endswith(ending) and len(r[2]) - len(ending) >= 4:
                    return (r[1], r[2])

    best = valid_results[0]

    # When the best split doesn't have a Fugenlaut but a close runner-up does,
    # prefer the Fugenlaut split (e.g., "Einkaufs+Trip" over "Einkauf+Strip")
    if len(valid_results) > 1 and not _has_fugenlaut(best[1]):
        for r in valid_results[1:]:
            if best[0] - r[0] > 0.5:
                break  # Too far from the best score
            if _has_fugenlaut(r[1]):
                return (r[1], r[2])

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
        min_score = -1.0  # Medium compounds (lowered to catch participial adjectives)
    elif _depth > 0:
        min_score = 0.5   # Stricter for recursive splits
    else:
        min_score = 0.4   # Normal compounds

    # Check if word looks like a participial adjective (ends in -end/-ende/etc.)
    prefer_participle = any(word.lower().endswith(e) for e in PARTICIPLE_ENDINGS)

    # Try to split the word
    split = _split_once(word, min_score, prefer_participle=prefer_participle)
    if not split:
        return None

    left, right = split

    # Validate: both parts should be reasonable length (min 3 chars)
    if len(left) < 3 or len(right) < 3:
        return None

    # Check if it's a derived word (Ausbildung, not Aus + Bildung)
    if _is_derived_word(word, [left, right]):
        return None

    # Validate that both parts are recognizable words (reject gibberish splits)
    # Clean the left part first to check the base form, not the linking form
    cleaned_left = _clean_compound_part(left)
    if not simplemma.is_known(cleaned_left, lang="de") or not simplemma.is_known(right, lang="de"):
        return None

    # Clean linking elements from left part
    left = cleaned_left

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

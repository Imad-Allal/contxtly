"""V2 compound splitter improvements.

Wraps v1's split_compound with four targeted fixes:

  1. Skip splitting when the input is already a known noun lemma.
     Prevents "Hinweis" → "Hin + Weis" false positives.

  2. Skip splitting when the input lemmatises to a known noun.
     Catches inflected forms like "Hinweise" → "Hinweis" (no split).

  3. Noun-aware part cleaning: when v1 cleans a Fugen-stripped part via
     simplemma and gets a verb infinitive ("Eil" → "eilen"), check the
     noun table first; if "Eil"/"Eile" is a known noun, prefer that.

  4. Deeper recursion (capped at depth 4 instead of 2) so very long
     compounds split fully (Krankenversicherungsbeitragsschuldner …).

Behaviour gracefully degrades to v1 when GERMAN_NOUN_LEMMAS is empty,
so the splitter still works on environments without migration 013.
"""

import simplemma

from languages.german import compounds as v1_compounds
from languages.german.dict_store import GERMAN_NOUN_LEMMAS


# Maximum recursion depth for splitting nested compounds.
_MAX_DEPTH = 4

# Common noun-forming Fugen patterns to try when checking a part against
# the noun lemma set ("Eil" → also try "Eile").
_NOUN_REINFLECTIONS = ("e", "en", "n", "er")


def _is_known_noun(word: str) -> bool:
    """O(1) check against the loaded noun lemma set."""
    return word.lower() in GERMAN_NOUN_LEMMAS


def _is_inflection_of_known_noun(word: str) -> bool:
    """True iff `word` is an *inflected* form of a known noun (different
    from its lemma). The bare lemma itself returns False — even if it's
    in the noun table — because compound nouns like "Sonnenblume" are
    valid noun lemmas AND legitimate split targets.
    """
    sm_lemma = simplemma.lemmatize(word, lang="de")
    if not sm_lemma:
        return False
    if sm_lemma.lower() == word.lower():
        return False  # word IS the lemma; don't pre-empt the splitter
    return _is_known_noun(sm_lemma)


def _looks_like_verb_infinitive(s: str) -> bool:
    """Cheap heuristic: lowercase, ends in -en, length >= 4."""
    return (
        len(s) >= 4
        and s == s.lower()
        and s.endswith("en")
    )


def _noun_aware_clean_part(part: str) -> str:
    """Like v1's _clean_compound_part, but prefers a noun candidate over
    a simplemma verb infinitive.

    Steps:
      1. If the part itself is a known noun → return as-is
      2. Try common noun-forming reinflections (Eil + e → Eile, Sonn + e
         → Sonne) and check each against the noun set
      3. Fall back to v1's cleaning logic
      4. Defensive: if v1 turned an uppercase noun-shaped part into a
         lowercase verb infinitive (e.g. "Eil" → "eilen"), reject and
         return the original part — German compounds are noun-headed,
         a verb-shaped cleaned part is almost certainly wrong
    """
    if _is_known_noun(part):
        return part

    if GERMAN_NOUN_LEMMAS:
        for suffix in _NOUN_REINFLECTIONS:
            candidate = part + suffix
            if _is_known_noun(candidate):
                # Capitalise to match noun convention (German nouns are
                # always capitalised; the input may be lower-case from
                # the splitter's internal normalisation)
                return candidate[0].upper() + candidate[1:]

    cleaned = v1_compounds._clean_compound_part(part)

    # Defensive check: if the input looked noun-shaped (capitalised) but
    # cleaning produced something verb-shaped (lowercase, -en infinitive),
    # the cleaner went wrong — keep the original.
    if (
        part
        and part[0].isupper()
        and _looks_like_verb_infinitive(cleaned)
        and not _is_known_noun(cleaned)
    ):
        return part

    return cleaned


def _split_recursive(word: str, depth: int = 0) -> list[str] | None:
    """Recursive split with deeper depth than v1 and noun-aware cleaning.

    This is a thin reimplementation of the bottom of v1's split_compound
    that swaps in our noun-aware cleaner and our depth limit. Everything
    else (CharSplit-based _split_once, validation, derived-word
    rejection) is reused from v1.
    """
    if depth > _MAX_DEPTH:
        return None
    if len(word) < 6:
        return None

    if len(word) >= 15:
        min_score = -1.0
    elif len(word) >= 10:
        min_score = -1.0
    elif depth > 0:
        min_score = 0.5
    else:
        min_score = 0.4

    prefer_participle = any(word.lower().endswith(e) for e in v1_compounds.PARTICIPLE_ENDINGS)

    split = v1_compounds._split_once(word, min_score, prefer_participle=prefer_participle)
    if not split:
        return None

    left, right = split

    if len(left) < 3 or len(right) < 3:
        return None

    if v1_compounds._is_derived_word(word, [left, right]):
        return None

    cleaned_left = _noun_aware_clean_part(left)

    # Validate: both parts should be recognisable. Prefer noun set when
    # populated; fall back to simplemma. The right part is the head noun
    # and is checked as-is (it's almost always already a clean noun).
    left_known = (
        _is_known_noun(cleaned_left)
        or simplemma.is_known(cleaned_left, lang="de")
        or simplemma.is_known(cleaned_left + "n", lang="de")
        or simplemma.is_known(cleaned_left + "en", lang="de")
    )
    right_known = (
        _is_known_noun(right)
        or simplemma.is_known(right, lang="de")
    )
    if not left_known or not right_known:
        return None

    left = cleaned_left

    result: list[str] = []
    if len(left) >= 8:  # try harder on shorter sub-parts than v1
        sub = _split_recursive(left, depth + 1)
        if sub:
            result.extend(sub)
        else:
            result.append(left)
    else:
        result.append(left)
    result.append(right)

    return result if len(result) > 1 else None


def split_compound(word: str) -> list[str] | None:
    """V2 split_compound entry point.

    Skip splitting only when the word is an *inflection* of a known
    noun (Hinweise → Hinweis → no split). Lemma forms — including
    compound lemmas like "Sonnenblume" — go through the splitter so
    valid compositions are recovered.

    When GERMAN_NOUN_LEMMAS is empty (migration 013 not applied), the
    inflection check is skipped and we behave exactly like v1.
    """
    if not word:
        return None

    if GERMAN_NOUN_LEMMAS and _is_inflection_of_known_noun(word):
        return None

    return _split_recursive(word)

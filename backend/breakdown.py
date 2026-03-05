from analyzer import WordAnalysis
from languages.base import describe_morphology

# Definite articles by language, case and gender
_ARTICLES: dict[str, dict[str, dict[str, str]]] = {
    "de": {
        "Nom": {"Masc": "der", "Fem": "die", "Neut": "das"},
        "Acc": {"Masc": "den", "Fem": "die", "Neut": "das"},
        "Dat": {"Masc": "dem", "Fem": "der", "Neut": "dem"},
        "Gen": {"Masc": "des", "Fem": "der", "Neut": "des"},
    },
    "fr": {
        "Nom": {"Masc": "le", "Fem": "la"},
    },
    "es": {
        "Nom": {"Masc": "el", "Fem": "la"},
    },
    "it": {
        "Nom": {"Masc": "il", "Fem": "la"},
    },
    "pt": {
        "Nom": {"Masc": "o", "Fem": "a"},
    },
    "nl": {
        "Nom": {"Masc": "de", "Fem": "de", "Neut": "het"},
    },
}


def _get_article(lang: str, case: str | None, gender: str | None) -> str:
    """Return the appropriate definite article for the given language, case and gender."""
    if not gender or lang not in _ARTICLES:
        return ""
    lang_articles = _ARTICLES[lang]
    # Fall back to Nom if the specific case isn't defined (e.g. for languages without full declension tables)
    case_articles = lang_articles.get(case or "Nom") or lang_articles.get("Nom", {})
    return case_articles.get(gender, "")


def generate_verb_breakdown(analysis: WordAnalysis, lemma_translation: str) -> str | None:
    """Generate breakdown for regular conjugated verbs (no separable/compound tense)."""
    if analysis.word_type != "conjugated_verb":
        return None

    morph_desc = describe_morphology(analysis.morph, include=["Tense", "Person", "Number", "Mood"])
    if morph_desc:
        return f"{analysis.lemma} ({lemma_translation}) → {analysis.text} ({morph_desc})"

    return None


def generate_noun_breakdown(analysis: WordAnalysis, translation: str) -> str | None:
    """Generate breakdown for singular nouns showing gender and case."""
    if analysis.word_type != "noun":
        return None

    gender = analysis.morph.get("Gender")
    case = analysis.morph.get("Case")
    morph_desc = describe_morphology(analysis.morph, include=["Gender", "Number", "Case"])
    if not morph_desc:
        return None

    article = _get_article(analysis.lang, case, gender)
    lemma_display = f"{article} {analysis.lemma}" if article else analysis.lemma
    return f"{lemma_display} ({translation}) → {morph_desc}"


def generate_plural_breakdown(analysis: WordAnalysis, singular_translation: str) -> str | None:
    """Generate breakdown for plural nouns."""
    if analysis.word_type != "plural_noun":
        return None

    text = analysis.text
    lemma = analysis.lemma

    gender = analysis.morph.get("Gender")
    gender_desc = describe_morphology(analysis.morph, include=["Gender"])
    morph_parts = [gender_desc] if gender_desc else []
    morph_parts.append("plural")
    morph_desc = ", ".join(morph_parts)

    if lemma != text:
        # Plural uses nominative article (dictionary form)
        article = _get_article(analysis.lang, "Nom", gender)
        lemma_display = f"{article} {lemma}" if article else lemma
        return f"{lemma_display} ({singular_translation}) → {text} ({morph_desc})"

    return None


def generate_compound_breakdown(compound_parts: list[tuple[str, str, str]]) -> str | None:
    """Generate breakdown for compound nouns.

    Args:
        compound_parts: List of (original_part, base_form, translation) tuples
    """
    if not compound_parts or len(compound_parts) < 2:
        return None

    # Format: "krank (sick) + Haus (house)" - using base form
    parts_str = " + ".join(f"{base} ({trans})" for _, base, trans in compound_parts)
    return parts_str


def generate_breakdown(
    analysis: WordAnalysis,
    base_translation: str,
    compound_parts: list[tuple[str, str, str]] | None = None,
) -> str | None:
    """
    Generate breakdown for a word based on its type (generic fallback).

    Language-specific breakdowns are handled by LanguageAnalysis.breakdown_fn
    in the pipeline before this function is called.

    Args:
        analysis: WordAnalysis from analyzer
        base_translation: Translation of the lemma/base form
        compound_parts: Optional list of (part, base, translation) for compounds

    Returns:
        Breakdown string or None if word is simple
    """
    if compound_parts:
        return generate_compound_breakdown(compound_parts)

    if analysis.word_type == "conjugated_verb":
        return generate_verb_breakdown(analysis, base_translation)

    if analysis.word_type == "noun":
        return generate_noun_breakdown(analysis, base_translation)

    if analysis.word_type == "plural_noun":
        return generate_plural_breakdown(analysis, base_translation)

    return None

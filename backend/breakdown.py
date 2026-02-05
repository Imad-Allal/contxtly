from analyzer import WordAnalysis
from languages.base import describe_morphology


def generate_verb_breakdown(analysis: WordAnalysis, lemma_translation: str) -> str | None:
    """Generate breakdown for regular conjugated verbs (no separable/compound tense)."""
    if analysis.word_type != "conjugated_verb":
        return None

    morph_desc = describe_morphology(analysis.morph, include=["Tense", "Person", "Number", "Mood"])
    if morph_desc:
        return f"{analysis.lemma} ({lemma_translation}) → {analysis.text} ({morph_desc})"

    return None


def generate_plural_breakdown(analysis: WordAnalysis, singular_translation: str) -> str | None:
    """Generate breakdown for plural nouns."""
    if analysis.word_type != "plural_noun":
        return None

    text = analysis.text
    lemma = analysis.lemma

    if lemma != text:
        return f"{lemma} ({singular_translation}) → {text} (plural)"

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

    if analysis.word_type == "plural_noun":
        return generate_plural_breakdown(analysis, base_translation)

    return None

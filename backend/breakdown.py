"""Breakdown generation for complex words."""

from analyzer import WordAnalysis
from languages.base import describe_morphology


def generate_verb_breakdown(analysis: WordAnalysis, lemma_translation: str) -> str | None:
    """Generate breakdown for conjugated verbs using spaCy morphology."""
    if analysis.word_type != "conjugated_verb":
        return None

    # If we detected a compound tense (Perfekt, Futur, etc.), use that
    if analysis.compound_tense:
        return f"{analysis.lemma} ({lemma_translation}) → {analysis.text} ({analysis.compound_tense})"

    # Otherwise, use spaCy's morphology for simple tenses
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


def generate_breakdown(
    analysis: WordAnalysis,
    base_translation: str,
    compound_parts: list[tuple[str, str]] | None = None,
) -> str | None:
    """
    Generate breakdown for a word based on its type.

    Args:
        analysis: WordAnalysis from analyzer
        base_translation: Translation of the lemma/base form
        compound_parts: Optional list of (part, translation) for compounds

    Returns:
        Breakdown string or None if word is simple
    """
    if analysis.word_type == "simple":
        return None

    if analysis.word_type == "conjugated_verb":
        return generate_verb_breakdown(analysis, base_translation)

    if analysis.word_type == "plural_noun":
        return generate_plural_breakdown(analysis, base_translation)

    if analysis.word_type == "compound_noun" and compound_parts:
        parts_str = " + ".join(f"{part} ({trans})" for part, trans in compound_parts)
        return parts_str

    if analysis.word_type == "compound_adjective" and compound_parts:
        parts_str = " + ".join(f"{part} ({trans})" for part, trans in compound_parts)
        return parts_str

    return None

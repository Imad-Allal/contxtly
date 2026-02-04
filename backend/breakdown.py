"""Breakdown generation for complex words."""

from analyzer import WordAnalysis
from languages.base import describe_morphology


def generate_verb_breakdown(analysis: WordAnalysis, lemma_translation: str) -> str | None:
    """Generate breakdown for conjugated verbs and separable verb prefixes."""
    if analysis.word_type not in ("conjugated_verb", "separable_prefix"):
        return None

    # Use separable verb infinitive if detected, otherwise use lemma
    infinitive = analysis.separable_verb or analysis.lemma

    # For separable verbs detected from prefix, use verb info
    if analysis.separable_verb_info:
        verb_text, verb_morph = analysis.separable_verb_info
        conjugated = f"{verb_text} + {analysis.text}"
        morph_desc = describe_morphology(verb_morph, include=["Tense", "Person", "Number", "Mood"])
        if morph_desc:
            return f"{infinitive} ({lemma_translation}) → {conjugated} ({morph_desc})"
        return f"{infinitive} ({lemma_translation}) → {conjugated}"

    # For separable verbs detected from verb stem, show the split form: "fängt + an"
    conjugated = analysis.text
    if analysis.separable_verb:
        # Extract prefix from separable verb (e.g., "anfangen" → "an")
        prefix = analysis.separable_verb.replace(analysis.lemma, "")
        conjugated = f"{analysis.text} + {prefix}"

    # If we detected a compound tense (Perfekt, Futur, etc.), use that
    if analysis.compound_tense:
        return f"{infinitive} ({lemma_translation}) → {conjugated} ({analysis.compound_tense})"

    # Otherwise, use spaCy's morphology for simple tenses
    morph_desc = describe_morphology(analysis.morph, include=["Tense", "Person", "Number", "Mood"])

    if morph_desc:
        return f"{infinitive} ({lemma_translation}) → {conjugated} ({morph_desc})"

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
    Generate breakdown for a word based on its type.

    Args:
        analysis: WordAnalysis from analyzer
        base_translation: Translation of the lemma/base form
        compound_parts: Optional list of (part, base, translation) for compounds

    Returns:
        Breakdown string or None if word is simple
    """
    # Compound words take priority
    if compound_parts:
        return generate_compound_breakdown(compound_parts)

    if analysis.word_type in ("conjugated_verb", "separable_prefix"):
        return generate_verb_breakdown(analysis, base_translation)

    if analysis.word_type == "simple":
        return None

    if analysis.word_type == "plural_noun":
        return generate_plural_breakdown(analysis, base_translation)

    return None

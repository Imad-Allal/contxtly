"""German language configuration."""

import spacy
from languages.base import LanguageConfig, LanguageModule


# German compound tense patterns
# (auxiliary_lemma, aux_tense, main_verbform) -> tense_name
GERMAN_COMPOUND_TENSES = {
    # Perfekt: haben/sein (present) + Partizip II
    ("haben", "Pres", "Part"): "Perfekt (present perfect)",
    ("sein", "Pres", "Part"): "Perfekt (present perfect)",
    # Plusquamperfekt: haben/sein (past) + Partizip II
    ("haben", "Past", "Part"): "Plusquamperfekt (past perfect)",
    ("sein", "Past", "Part"): "Plusquamperfekt (past perfect)",
    # Futur I: werden (present) + Infinitiv
    ("werden", "Pres", "Inf"): "Futur I (future)",
    # Futur II: werden + Partizip II + haben/sein (detected as Part)
    ("werden", "Pres", "Part"): "Futur II (future perfect)",
    # Konjunktiv II (würde + Infinitiv)
    ("werden", "Sub", "Inf"): "Konjunktiv II (subjunctive)",
}

# Auxiliary verbs to look for
GERMAN_AUXILIARIES = {"haben", "sein", "werden"}


def detect_compound_tense(target_word: str, doc: spacy.tokens.Doc) -> str | None:
    """
    Detect German compound tenses by analyzing auxiliary + main verb patterns.

    Args:
        target_word: The word being translated (e.g., "gesprochen")
        doc: spaCy Doc of the full sentence context

    Returns:
        Compound tense name or None if not a compound tense
    """
    main_verb = None
    aux_verb = None

    for token in doc:
        # Find the target word
        if token.text.lower() == target_word.lower():
            main_verb = token
        # Find auxiliary verb
        if token.lemma_ in GERMAN_AUXILIARIES:
            aux_verb = token

    if not (aux_verb and main_verb):
        return None

    # Get morphological features
    aux_morph = dict(aux_verb.morph.to_dict())
    main_morph = dict(main_verb.morph.to_dict())

    aux_lemma = aux_verb.lemma_
    aux_tense = aux_morph.get("Tense") or aux_morph.get("Mood", "")
    main_form = main_morph.get("VerbForm", "")

    # Look up compound tense
    key = (aux_lemma, aux_tense, main_form)
    return GERMAN_COMPOUND_TENSES.get(key)


class German(LanguageModule):
    """German language support with compound word handling."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="de",
            name="German",
            spacy_model="de_core_news_sm",
            # German-specific: compound word splitting
            supports_compounds=True,
            compound_min_length=10, #TODO try other values
            compound_prefixes={"ver", "be", "ge", "ent", "er", "zer", "miss", "un", "ur"},
            compound_linking_patterns=[
                ("ungs", "ung"),      # Verhandlungs -> Verhandlung
                ("ions", "ion"),      # Kommunikations -> Kommunikation
                ("täts", "tät"),      # Universitäts -> Universität
                ("heits", "heit"),    # Freiheits -> Freiheit
                ("keits", "keit"),    # Möglichkeits -> Möglichkeit
                ("schafts", "schaft"),  # Gesellschafts -> Gesellschaft
                ("eits", "eit"),      # Arbeits -> Arbeit
            ],
            # German-specific: separable verbs need special handling
            translation_prompt_addition='''
Important for German: Check if "{word}" is part of a separable verb (e.g., "setzten...zusammen" = zusammensetzen, "fing...an" = anfangen). If so, translate the FULL verb, not just the conjugated part.''',
        )

    def detect_compound_tense(self, target_word: str, doc: spacy.tokens.Doc) -> str | None:
        """Detect German compound tenses from sentence context."""
        return detect_compound_tense(target_word, doc)

"""German language module."""

from models import TokenRef
from languages.base import LanguageConfig, LanguageModule, LanguageAnalysis, describe_morphology
from languages.german.compounds import split_compound
from languages.german.verbs import detect_separable_verb, detect_separable_verb_from_prefix, detect_compound_tense
from languages.german.collocations import CollocationInfo, detect_verb_preposition_collocation


class German(LanguageModule):
    """German language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="de",
            name="German",
            spacy_model="de_core_news_sm",
        )

    def split_compound(self, word: str) -> list[str] | None:
        """Split a compound word into parts."""
        return split_compound(word)

    def analyze(self, word: str, token, doc, morph: dict[str, str]) -> LanguageAnalysis | None:
        """Run all German-specific detections and return a LanguageAnalysis."""

        # --- Collocation detection (highest priority) ---
        collocation = detect_verb_preposition_collocation(word, doc)
        if collocation:
            return self._analyze_collocation(word, token, collocation, morph)

        # --- Separable verb detection (from verb stem) ---
        sv_result = detect_separable_verb(word, doc)
        if sv_result:
            infinitive, prefix_ref = sv_result
            return self._analyze_separable_from_verb(word, token, infinitive, prefix_ref, morph)

        # --- Separable verb detection (from prefix/particle) ---
        svp_result = detect_separable_verb_from_prefix(word, doc)
        if svp_result:
            infinitive, verb_text, verb_morph, verb_offset = svp_result
            return self._analyze_separable_from_prefix(word, infinitive, verb_text, verb_morph, verb_offset)

        # --- Compound tense detection ---
        compound_tense = detect_compound_tense(word, doc)
        if compound_tense:
            return self._analyze_compound_tense(word, token, compound_tense, morph)

        return None

    def _analyze_collocation(
        self, word: str, token, collocation: CollocationInfo, morph: dict[str, str]
    ) -> LanguageAnalysis:
        """Build LanguageAnalysis for a verb+preposition collocation."""
        is_verb = token.pos_ == "VERB"
        word_type = "collocation_verb" if is_verb else "collocation_prep"

        # Extract display pattern: "verb + prep"
        prep_text = next((r.text for r in collocation.related if r.text.lower() != collocation.verb), "")
        pattern = f"{collocation.verb} + {prep_text}"

        # Capture data for breakdown closure
        col_pattern = collocation.pattern
        col_related = collocation.related
        selected_text = word

        def breakdown_fn(analysis, base_translation):
            all_parts = [selected_text] + [r.text for r in col_related]
            conjugated = " + ".join(all_parts)
            morph_desc = ""
            if word_type == "collocation_verb":
                morph_desc = describe_morphology(morph, include=["Tense", "Person", "Number", "Mood"])
            if morph_desc:
                return f"{col_pattern} ({base_translation}) → {conjugated} ({morph_desc})"
            return f"{col_pattern} ({base_translation}) → {conjugated}"

        return LanguageAnalysis(
            translate=collocation.verb,
            lemma=collocation.verb,
            word_type=word_type,
            related=[TokenRef(r.text, r.offset) for r in collocation.related],
            pattern=pattern,
            llm_hint=collocation.pattern,
            breakdown_fn=breakdown_fn,
        )

    def _analyze_separable_from_verb(
        self, word: str, token, infinitive: str, prefix_ref: TokenRef, morph: dict[str, str]
    ) -> LanguageAnalysis:
        """Build LanguageAnalysis when user selected the verb stem of a separable verb."""
        lemma = token.lemma_
        selected_text = word

        def breakdown_fn(analysis, base_translation):
            prefix = infinitive.replace(lemma, "")
            conjugated = f"{selected_text} + {prefix}"
            morph_desc = describe_morphology(morph, include=["Tense", "Person", "Number", "Mood"])
            if morph_desc:
                return f"{infinitive} ({base_translation}) → {conjugated} ({morph_desc})"
            return f"{infinitive} ({base_translation}) → {conjugated}"

        return LanguageAnalysis(
            translate=infinitive,
            lemma=infinitive,
            word_type="conjugated_verb",
            related=[prefix_ref],
            breakdown_fn=breakdown_fn,
        )

    def _analyze_separable_from_prefix(
        self, word: str, infinitive: str, verb_text: str, verb_morph: dict[str, str], verb_offset: int
    ) -> LanguageAnalysis:
        """Build LanguageAnalysis when user selected the prefix/particle of a separable verb."""
        selected_text = word

        def breakdown_fn(analysis, base_translation):
            conjugated = f"{verb_text} + {selected_text}"
            morph_desc = describe_morphology(verb_morph, include=["Tense", "Person", "Number", "Mood"])
            if morph_desc:
                return f"{infinitive} ({base_translation}) → {conjugated} ({morph_desc})"
            return f"{infinitive} ({base_translation}) → {conjugated}"

        return LanguageAnalysis(
            translate=infinitive,
            lemma=infinitive,
            word_type="separable_prefix",
            related=[TokenRef(verb_text, verb_offset)],
            breakdown_fn=breakdown_fn,
        )

    def _analyze_compound_tense(
        self, word: str, token, compound_tense: str, morph: dict[str, str]
    ) -> LanguageAnalysis:
        """Build LanguageAnalysis for a verb in a compound tense (Perfekt, Futur, etc.)."""
        lemma = token.lemma_
        selected_text = word

        def breakdown_fn(analysis, base_translation):
            return f"{lemma} ({base_translation}) → {selected_text} ({compound_tense})"

        return LanguageAnalysis(
            word_type="conjugated_verb",
            breakdown_fn=breakdown_fn,
        )

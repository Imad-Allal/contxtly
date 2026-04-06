"""
CI tests for German word analysis accuracy.

Tests the deterministic analyzer layer (no LLM calls).
Each test verifies: word_type classification, lemma resolution, and compound splitting.
"""

import pytest
from analyzer import analyze_word
from languages.german.compounds import split_compound


# ---------------------------------------------------------------------------
# Compound words — split_compound() tests
# ---------------------------------------------------------------------------
COMPOUND_SPLIT_CASES = [
    # (word, expected_parts)
    ("Gehaltserhöhung", ["Gehalt", "Erhöhung"]),
    ("Eilmeldung", ["Eil", "Meldung"]),
    ("Handschuh", ["Hand", "Schuh"]),
    ("Kühlschrank", ["Kühl", "Schrank"]),
    ("Flughafen", ["Flug", "Hafen"]),
    ("Weihnachtsbaum", ["Weihnacht", "Baum"]),
    ("Briefkasten", ["Brief", "Kasten"]),
    ("Rathaus", ["Rat", "Haus"]),
    ("Spielplatz", ["Spiel", "Platz"]),
    ("Fahrkarte", ["Fahr", "Karte"]),
    ("Schlafzimmer", ["Schlaf", "Zimmer"]),
    ("Kindergarten", ["Kinder", "Garten"]),
    ("Haustür", ["Haus", "Tür"]),
    ("Regenschirm", ["Regen", "Schirm"]),
    ("Tageslicht", ["Tag", "Licht"]),
    ("Wohnzimmer", ["Wohn", "Zimmer"]),
    ("Zeitschrift", ["Zeit", "Schrift"]),
    ("Krankenhaus", ["Kranken", "Haus"]),
    ("Straßenbahn", ["Straßen", "Bahn"]),
    ("Königsblauen", ["König", "Blauen"]),
    ("Trinkwasser", ["Trink", "Wasser"]),
    ("Führerschein", ["Führer", "Schein"]),
    ("Geburtstag", ["Geburt", "Tag"]),
    ("Sonnenschein", ["Sonne", "Schein"]),
    ("Grundschule", ["Grund", "Schule"]),
    ("Hauptstadt", ["Haupt", "Stadt"]),
    ("Wanderschuh", ["Wander", "Schuh"]),
    ("Bahnhof", ["Bahn", "Hof"]),
    ("Preiserhöhung", ["Preis", "Erhöhung"]),
]

# Compounds that should NOT be split (derived words)
NOT_COMPOUND_CASES = [
    "Ausbildung",
    "Verhandlung",
    "Erfahrung",
    "Gesellschaft",
    "Verfehlung",
    "Entscheidung",
    "Bedeutung",
    "Entwicklung",
    "Verbindung",
    "Einkommen",
]


class TestCompoundSplitting:
    """Test compound word splitting accuracy."""

    @pytest.mark.parametrize("word,expected_parts", COMPOUND_SPLIT_CASES, ids=[c[0] for c in COMPOUND_SPLIT_CASES])
    def test_compound_splits(self, word, expected_parts):
        """Verify compound words are split correctly."""
        parts = split_compound(word)
        assert parts is not None, f"'{word}' should split into parts"
        parts_lower = [p.lower() for p in parts]
        expected_lower = [p.lower() for p in expected_parts]
        assert parts_lower == expected_lower, (
            f"'{word}' split into {parts}, expected {expected_parts}"
        )

    @pytest.mark.parametrize("word", NOT_COMPOUND_CASES)
    def test_derived_words_not_split(self, word):
        """Derived words should NOT be split as compounds."""
        parts = split_compound(word)
        assert parts is None, f"'{word}' is derived, should not be split (got {parts})"

    def test_compound_word_type_in_pipeline(self):
        """Compound detection sets word_type via pipeline, not analyze_word.
        analyze_word returns 'noun' for compounds; pipeline overrides to 'compound'."""
        result = analyze_word("Krankenhaus", context="Er ging ins Krankenhaus.", source_lang="de")
        # analyze_word classifies as noun — compound detection happens in pipeline
        assert result.word_type == "noun"
        # But split_compound should find parts
        parts = split_compound("Krankenhaus")
        assert parts is not None and len(parts) >= 2


# ---------------------------------------------------------------------------
# Conjugated verbs (word_type detection)
# ---------------------------------------------------------------------------
CONJUGATED_VERB_TYPE_CASES = [
    # (word, context)
    ("beschloss", "Der Bundestag beschloss das neue Gesetz."),
    ("geht", "Er geht nach Hause."),
    ("lief", "Sie lief schnell."),
    ("spricht", "Sie spricht Deutsch."),
    ("nahm", "Er nahm das Buch."),
    ("flog", "Der Vogel flog weg."),
    ("trug", "Sie trug einen Hut."),
    ("gab", "Er gab mir das Buch."),
    ("fand", "Sie fand den Schlüssel."),
    ("blieb", "Er blieb zu Hause."),
    ("kam", "Sie kam spät an."),
    ("schrieb", "Er schrieb einen Brief."),
    ("schlief", "Das Kind schlief ein."),
    ("fuhr", "Sie fuhr nach Berlin."),
    ("sang", "Er sang ein Lied."),
]


class TestConjugatedVerbs:
    """Test verb conjugation detection."""

    @pytest.mark.parametrize(
        "word,context",
        CONJUGATED_VERB_TYPE_CASES,
        ids=[c[0] for c in CONJUGATED_VERB_TYPE_CASES],
    )
    def test_verb_type_detected(self, word, context):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "conjugated_verb", (
            f"'{word}' should be 'conjugated_verb', got '{result.word_type}'"
        )


# Verbs where spaCy correctly resolves the lemma
VERB_LEMMA_CORRECT_CASES = [
    ("geht", "Er geht nach Hause.", "gehen"),
    ("lief", "Sie lief schnell.", "laufen"),
    ("spricht", "Sie spricht Deutsch.", "sprechen"),
    ("nahm", "Er nahm das Buch.", "nehmen"),
    ("gab", "Er gab mir das Buch.", "geben"),
    ("fand", "Sie fand den Schlüssel.", "finden"),
    ("blieb", "Er blieb zu Hause.", "bleiben"),
    ("kam", "Sie kam spät an.", "kommen"),
    ("trug", "Sie trug einen Hut.", "tragen"),
    ("flog", "Der Vogel flog weg.", "fliegen"),
]


class TestVerbLemmas:
    """Test verb lemma resolution."""

    @pytest.mark.parametrize(
        "word,context,expected_lemma",
        VERB_LEMMA_CORRECT_CASES,
        ids=[c[0] for c in VERB_LEMMA_CORRECT_CASES],
    )
    def test_verb_lemma_correct(self, word, context, expected_lemma):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.lemma == expected_lemma, (
            f"'{word}' lemma should be '{expected_lemma}', got '{result.lemma}'"
        )


# ---------------------------------------------------------------------------
# Morphology (person, number, tense)
# ---------------------------------------------------------------------------
MORPHOLOGY_CASES = [
    # (word, context, expected_morph_subset)
    ("ausrichtest", "Wenn du die Maschine ausrichtest, funktioniert sie besser.", {"Person": "2", "Number": "Sing"}),
    ("geht", "Er geht nach Hause.", {"Person": "3", "Number": "Sing", "Tense": "Pres"}),
    ("spielen", "Wir spielen Fußball.", {"Person": "1", "Number": "Plur"}),
    ("fahrt", "Ihr fahrt nach Berlin.", {"Person": "2", "Number": "Plur"}),
    ("schreibst", "Du schreibst einen Brief.", {"Person": "2", "Number": "Sing"}),
    ("arbeiten", "Sie arbeiten hart.", {"Person": "3", "Number": "Plur"}),
]


class TestMorphology:
    """Test morphological feature extraction."""

    @pytest.mark.parametrize(
        "word,context,expected_morph",
        MORPHOLOGY_CASES,
        ids=[c[0] for c in MORPHOLOGY_CASES],
    )
    def test_morph_features(self, word, context, expected_morph):
        result = analyze_word(word, context=context, source_lang="de")
        for key, val in expected_morph.items():
            assert result.morph.get(key) == val, (
                f"'{word}' morph['{key}'] should be '{val}', got '{result.morph.get(key)}' "
                f"(full morph: {result.morph})"
            )


# ---------------------------------------------------------------------------
# Separable verbs
# ---------------------------------------------------------------------------
SEPARABLE_VERB_FROM_VERB_CASES = [
    # (selected_word, context, expected_infinitive)
    ("ziehe", "Ich ziehe mich an.", "anziehen"),
    ("fängt", "Das Spiel fängt um acht an.", "anfangen"),
    ("steht", "Er steht jeden Morgen früh auf.", "aufstehen"),
    ("macht", "Sie macht die Tür zu.", "zumachen"),
    ("kommt", "Er kommt morgen an.", "ankommen"),
    ("stellt", "Er stellt das Buch zurück.", "zurückstellen"),
    ("ruft", "Sie ruft ihre Mutter an.", "anrufen"),
]

SEPARABLE_VERB_FROM_PREFIX_CASES = [
    # (selected_prefix, context, expected_infinitive)
    ("an", "Ich ziehe mich an.", "anziehen"),
    ("auf", "Er steht jeden Morgen früh auf.", "aufstehen"),
    ("zu", "Sie macht die Tür zu.", "zumachen"),
    ("nieder", "Er legte das Buch nieder.", "niederlegen"),
]


class TestSeparableVerbs:
    """Test separable verb detection."""

    @pytest.mark.parametrize(
        "word,context,expected_inf",
        SEPARABLE_VERB_FROM_VERB_CASES,
        ids=[f"{c[0]}->{c[2]}" for c in SEPARABLE_VERB_FROM_VERB_CASES],
    )
    def test_separable_from_verb(self, word, context, expected_inf):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.lang_analysis is not None, (
            f"'{word}' in '{context}' should have lang_analysis (separable verb)"
        )
        assert result.lang_analysis.lemma == expected_inf, (
            f"'{word}' infinitive should be '{expected_inf}', got '{result.lang_analysis.lemma}'"
        )

    @pytest.mark.parametrize(
        "word,context,expected_inf",
        SEPARABLE_VERB_FROM_PREFIX_CASES,
        ids=[f"{c[0]}->{c[2]}" for c in SEPARABLE_VERB_FROM_PREFIX_CASES],
    )
    def test_separable_from_prefix(self, word, context, expected_inf):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "separable_prefix", (
            f"Prefix '{word}' should be 'separable_prefix', got '{result.word_type}'"
        )
        assert result.lang_analysis is not None
        assert result.lang_analysis.lemma == expected_inf, (
            f"Prefix '{word}' infinitive should be '{expected_inf}', got '{result.lang_analysis.lemma}'"
        )


# ---------------------------------------------------------------------------
# Modal verb + infinitive
# ---------------------------------------------------------------------------
MODAL_INFINITIVE_CASES = [
    # (word, context) — infinitive governed by a modal verb should be classified as verb
    ("begrenzen", "Die Regierung will jetzt unter anderem Preiserhöhungen begrenzen."),
    ("schwimmen", "Er kann gut schwimmen."),
    ("arbeiten", "Sie muss morgen arbeiten."),
    ("stehlen", "Du sollst nicht stehlen."),
    ("gehen", "Ich darf heute früher gehen."),
    ("lesen", "Er möchte ein Buch lesen."),
    ("spielen", "Die Kinder wollen draußen spielen."),
    ("helfen", "Ich kann dir helfen."),
]


class TestModalInfinitive:
    """Test modal verb + infinitive detection."""

    @pytest.mark.parametrize(
        "word,context",
        MODAL_INFINITIVE_CASES,
        ids=[c[0] for c in MODAL_INFINITIVE_CASES],
    )
    def test_modal_infinitive_is_verb(self, word, context):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "conjugated_verb", (
            f"'{word}' in '{context}' should be 'conjugated_verb' (modal + infinitive), "
            f"got '{result.word_type}'"
        )


# ---------------------------------------------------------------------------
# Zu-infinitive should NOT be detected as separable verb
# ---------------------------------------------------------------------------
ZU_INFINITIVE_NOT_SEPARABLE_CASES = [
    # (word, context) — "zu" is infinitive particle, not a separable prefix
    ("gehen", "Ich habe beschlossen, heute früher zu gehen."),
    ("öffnen", "Er versuchte, die Tür zu öffnen."),
    ("arbeiten", "Sie hat angefangen, zu arbeiten."),
    ("lesen", "Er hat keine Lust, das Buch zu lesen."),
    ("schlafen", "Das Kind weigert sich, zu schlafen."),
]


class TestZuInfinitive:
    """Zu-infinitive particle must not trigger separable verb detection."""

    @pytest.mark.parametrize(
        "word,context",
        ZU_INFINITIVE_NOT_SEPARABLE_CASES,
        ids=[c[0] for c in ZU_INFINITIVE_NOT_SEPARABLE_CASES],
    )
    def test_zu_infinitive_not_separable(self, word, context):
        result = analyze_word(word, context=context, source_lang="de")
        # Should NOT be detected as a separable verb with "zu" prefix
        if result.lang_analysis and result.lang_analysis.lemma:
            assert not result.lang_analysis.lemma.startswith("zu"), (
                f"'{word}' in '{context}' should not be detected as separable 'zu{word}', "
                f"got '{result.lang_analysis.lemma}'"
            )


# ---------------------------------------------------------------------------
# Compound tenses (Perfekt, Plusquamperfekt, Futur, Passiv)
# ---------------------------------------------------------------------------
COMPOUND_TENSE_CASES = [
    # (word, context, expected_tense_substring)
    ("gegessen", "Ich habe gegessen.", "Perfekt"),
    ("beschlossen", "Sie haben beschlossen, das Projekt zu starten.", "Perfekt"),
    ("aufgerufen", "Die Vereinigung hat die Piloten aufgerufen.", "Perfekt"),
    ("gegangen", "Er ist nach Hause gegangen.", "Perfekt"),
    ("gefahren", "Wir sind nach Berlin gefahren.", "Perfekt"),
    ("geschwommen", "Sie ist ins Meer geschwommen.", "Perfekt"),
    ("gelaufen", "Er ist schnell gelaufen.", "Perfekt"),
    ("geschrieben", "Er hat einen Brief geschrieben.", "Perfekt"),
    ("gelesen", "Sie hat das Buch gelesen.", "Perfekt"),
    ("gesprochen", "Wir haben darüber gesprochen.", "Perfekt"),
    # Plusquamperfekt
    ("gegessen", "Ich hatte schon gegessen.", "Plusquamperfekt"),
    ("gefahren", "Wir waren nach Berlin gefahren.", "Plusquamperfekt"),
    # Futur I
    ("kommen", "Er wird morgen kommen.", "Futur"),
    # Passiv
    ("gebaut", "Das Haus wird gebaut.", "passiv"),
]


class TestCompoundTenses:
    """Test compound tense detection (Perfekt, Plusquamperfekt, Futur, Passiv)."""

    @pytest.mark.parametrize(
        "word,context,tense_hint",
        COMPOUND_TENSE_CASES,
        ids=[f"{c[0]}-{c[2]}" for c in COMPOUND_TENSE_CASES],
    )
    def test_compound_tense_detected(self, word, context, tense_hint):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "conjugated_verb", (
            f"'{word}' in '{context}' should be 'conjugated_verb', got '{result.word_type}'"
        )
        # Check the breakdown contains the tense hint
        assert result.lang_analysis is not None, (
            f"'{word}' should have lang_analysis for compound tense"
        )
        assert result.lang_analysis.breakdown_fn is not None
        breakdown = result.lang_analysis.breakdown_fn(result, "test")
        assert tense_hint.lower() in breakdown.lower(), (
            f"'{word}' breakdown should mention '{tense_hint}', got '{breakdown}'"
        )


# ---------------------------------------------------------------------------
# Plural nouns
# ---------------------------------------------------------------------------
PLURAL_NOUN_CASES = [
    # (word, context, expected_lemma)
    ("Häuser", "Die Häuser sind groß.", "Haus"),
    ("Kinder", "Die Kinder spielen.", "Kind"),
    ("Bücher", "Die Bücher liegen auf dem Tisch.", "Buch"),
    ("Männer", "Die Männer arbeiten.", "Mann"),
    ("Frauen", "Die Frauen sind klug.", "Frau"),
    ("Hunde", "Die Hunde bellen.", "Hund"),
    ("Katzen", "Die Katzen schlafen.", "Katze"),
    ("Autos", "Die Autos fahren schnell.", "Auto"),
    ("Hinweise", "Es gibt Hinweise auf den Täter.", "Hinweis"),
    ("Ärzte", "Die Ärzte helfen den Patienten.", "Arzt"),
    ("Länder", "Die Länder sind verschieden.", "Land"),
    ("Brüder", "Die Brüder spielen zusammen.", "Bruder"),
]


class TestPluralNouns:
    """Test plural noun detection and lemma resolution."""

    @pytest.mark.parametrize(
        "word,context,expected_lemma",
        PLURAL_NOUN_CASES,
        ids=[c[0] for c in PLURAL_NOUN_CASES],
    )
    def test_plural_detected(self, word, context, expected_lemma):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "plural_noun", (
            f"'{word}' should be 'plural_noun', got '{result.word_type}'"
        )

    @pytest.mark.parametrize(
        "word,context,expected_lemma",
        PLURAL_NOUN_CASES,
        ids=[c[0] for c in PLURAL_NOUN_CASES],
    )
    def test_plural_lemma(self, word, context, expected_lemma):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.lemma == expected_lemma, (
            f"'{word}' lemma should be '{expected_lemma}', got '{result.lemma}'"
        )


# ---------------------------------------------------------------------------
# Singular nouns (gender detection)
# ---------------------------------------------------------------------------
SINGULAR_NOUN_CASES = [
    # (word, context, expected_gender)
    ("Verfehlung", "Das war eine schwere Verfehlung.", "Fem"),
    ("Haus", "Das Haus ist groß.", "Neut"),
    ("Mann", "Der Mann geht.", "Masc"),
    ("Frau", "Die Frau liest.", "Fem"),
    ("Kind", "Das Kind spielt.", "Neut"),
    ("Tisch", "Der Tisch ist neu.", "Masc"),
    ("Schule", "Die Schule ist alt.", "Fem"),
    ("Buch", "Das Buch ist interessant.", "Neut"),
    ("Hund", "Der Hund bellt.", "Masc"),
    ("Stadt", "Die Stadt ist schön.", "Fem"),
]


class TestSingularNouns:
    """Test singular noun detection with gender."""

    @pytest.mark.parametrize(
        "word,context,expected_gender",
        SINGULAR_NOUN_CASES,
        ids=[c[0] for c in SINGULAR_NOUN_CASES],
    )
    def test_noun_type(self, word, context, expected_gender):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "noun", (
            f"'{word}' should be 'noun', got '{result.word_type}'"
        )

    @pytest.mark.parametrize(
        "word,context,expected_gender",
        SINGULAR_NOUN_CASES,
        ids=[c[0] for c in SINGULAR_NOUN_CASES],
    )
    def test_noun_gender(self, word, context, expected_gender):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.morph.get("Gender") == expected_gender, (
            f"'{word}' gender should be '{expected_gender}', got '{result.morph.get('Gender')}'"
        )


# ---------------------------------------------------------------------------
# Lassen constructions
# ---------------------------------------------------------------------------
LASSEN_FROM_LASSEN_CASES = [
    # (selected "lässt/lassen", context, expected_canonical)
    ("lässt", "Sie lässt das Auto reparieren.", "reparieren lassen"),
    ("lässt", "Das lässt sich erklären.", "sich erklären lassen"),
    ("lässt", "Er lässt mich warten.", "warten lassen"),
]


class TestLassenConstructions:
    """Test verb + lassen construction detection."""

    @pytest.mark.parametrize(
        "word,context,expected_canonical",
        LASSEN_FROM_LASSEN_CASES,
        ids=[f"{c[0]}-{c[2].replace(' ', '_')}" for c in LASSEN_FROM_LASSEN_CASES],
    )
    def test_lassen_from_lassen(self, word, context, expected_canonical):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.lang_analysis is not None, (
            f"'{word}' in '{context}' should detect lassen construction"
        )
        assert result.lang_analysis.lemma == expected_canonical, (
            f"'{word}' canonical should be '{expected_canonical}', got '{result.lang_analysis.lemma}'"
        )


# ---------------------------------------------------------------------------
# Known issues / expected failures (from todos.txt)
# ---------------------------------------------------------------------------
class TestKnownIssues:
    """Tests for known issues. Marked xfail until fixed."""

    @pytest.mark.xfail(reason="einzugießen (zu-infinitive) not detected as separable verb")
    def test_einzugiessen_separable(self):
        context = "Heinrich stellte einen Teller vor jeden der drei Männer und fing an, den Wein einzugießen."
        result = analyze_word("einzugießen", context=context, source_lang="de")
        assert result.word_type != "simple", (
            f"'einzugießen' should not be 'simple', should detect as separable verb (eingießen)"
        )

    @pytest.mark.xfail(reason="spaCy lemmatizes beschloss incorrectly")
    def test_beschloss_lemma(self):
        result = analyze_word("beschloss", context="Der Bundestag beschloss das neue Gesetz.", source_lang="de")
        assert result.lemma == "beschließen", (
            f"'beschloss' lemma should be 'beschließen', got '{result.lemma}'"
        )

    @pytest.mark.xfail(reason="spaCy lemmatizes gegessen incorrectly")
    def test_gegessen_lemma(self):
        result = analyze_word("gegessen", context="Ich habe gegessen.", source_lang="de")
        assert result.lemma == "essen", (
            f"'gegessen' lemma should be 'essen', got '{result.lemma}'"
        )

    @pytest.mark.xfail(reason="spaCy lemmatizes wusste incorrectly")
    def test_wusste_lemma(self):
        result = analyze_word("wusste", context="Ich wusste das nicht.", source_lang="de")
        assert result.lemma == "wissen", (
            f"'wusste' lemma should be 'wissen', got '{result.lemma}'"
        )

    @pytest.mark.xfail(reason="spaCy misclassifies liest Person as 3rd instead of 2nd")
    def test_liest_person(self):
        result = analyze_word("liest", context="Du liest ein Buch.", source_lang="de")
        assert result.morph.get("Person") == "2", (
            f"'liest' Person should be '2', got '{result.morph.get('Person')}'"
        )

    @pytest.mark.xfail(reason="lassen not detected when selecting the infinitive verb")
    def test_lassen_from_infinitive(self):
        result = analyze_word("reparieren", context="Sie lässt das Auto reparieren.", source_lang="de")
        assert result.lang_analysis is not None, (
            "'reparieren' should detect lassen construction when selected"
        )

    @pytest.mark.xfail(reason="teilnehmen detected as NVV 'Kurs nehmen' instead of separable verb")
    def test_teilnehmen_separable(self):
        result = analyze_word("nimmt", context="Sie nimmt an dem Kurs teil.", source_lang="de")
        assert result.lang_analysis is not None
        assert result.lang_analysis.lemma == "teilnehmen", (
            f"'nimmt' infinitive should be 'teilnehmen', got '{result.lang_analysis.lemma}'"
        )

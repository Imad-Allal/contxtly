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
    ("Eilmeldung", ["eilen", "Meldung"]),
    ("Handschuh", ["Hand", "Schuh"]),
    ("Kühlschrank", ["Kühl", "Schrank"]),
    ("Flughafen", ["Flug", "Hafen"]),
    ("Weihnachtsbaum", ["Weihnacht", "Baum"]),
    ("Briefkasten", ["Brief", "Kasten"]),
    ("Rathaus", ["Rat", "Haus"]),
    ("Spielplatz", ["Spiel", "Platz"]),
    ("Fahrkarte", ["fahren", "Karte"]),
    ("Schlafzimmer", ["Schlaf", "Zimmer"]),
    ("Kindergarten", ["Kind", "Garten"]),
    ("Haustür", ["Haus", "Tür"]),
    ("Regenschirm", ["Regen", "Schirm"]),
    ("Tageslicht", ["Tag", "Licht"]),
    ("Wohnzimmer", ["wohnen", "Zimmer"]),
    ("Zeitschrift", ["Zeit", "Schrift"]),
    ("Krankenhaus", ["Kranke", "Haus"]),
    ("Straßenbahn", ["Straße", "Bahn"]),
    ("Königsblauen", ["König", "Blauen"]),
    ("Trinkwasser", ["trinken", "Wasser"]),
    ("Führerschein", ["Führer", "Schein"]),
    ("Geburtstag", ["Geburt", "Tag"]),
    ("Sonnenschein", ["Sonne", "Schein"]),
    ("Grundschule", ["Grund", "Schule"]),
    ("Hauptstadt", ["Haupt", "Stadt"]),
    ("Wanderschuh", ["Wander", "Schuh"]),
    ("Bahnhof", ["Bahn", "Hof"]),
    ("Preiserhöhung", ["Preis", "Erhöhung"]),
    ("Arbeitstag", ["Arbeit", "Tag"]),
    ("Bundesland", ["Bund", "Land"]),
    ("Fußball", ["Fuß", "Ball"]),
    ("Hallenbad", ["Halle", "Bad"]),
    ("Jahreszeit", ["Jahr", "Zeit"]),
    ("Lesesaal", ["Lese", "Saal"]),
    ("Mittagessen", ["Mittag", "Essen"]),
    ("Nachttisch", ["Nacht", "Tisch"]),
    ("Parkplatz", ["Park", "Platz"]),
    ("Reisebüro", ["Reise", "Büro"]),
    ("Schreibtisch", ["schreiben", "Tisch"]),
    ("Stadtpark", ["Stadt", "Park"]),
    ("Tankstelle", ["Tank", "Stelle"]),
    ("Urlaubsreise", ["Urlaub", "Reise"]),
    ("Wartezimmer", ["Wart", "Zimmer"]),
    ("Zugfahrt", ["Zug", "Fahrt"]),
    ("Abendessen", ["Abend", "Essen"]),
    ("Badezimmer", ["Bad", "Zimmer"]),
    ("Busfahrer", ["Bus", "Fahrer"]),
    ("Dachboden", ["Dach", "Boden"]),
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
    "Beziehung",
    "Beschäftigung",
    "Überzeugung",
    "Versicherung",
    "Verwaltung",
    "Bewegung",
    "Hoffnung",
    "Leistung",
    "Meinung",
    "Sammlung",
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
    ("brach", "Er brach das Glas."),
    ("fragte", "Sie fragte die Lehrerin."),
    ("dachte", "Er dachte laut nach."),
    ("kaufte", "Sie kaufte ein neues Kleid."),
    ("wohnte", "Er wohnte in Berlin."),
    ("öffnete", "Sie öffnete die Tür."),
    ("schloss", "Er schloss das Fenster."),
    ("begann", "Das Konzert begann pünktlich."),
    ("verlor", "Er verlor seinen Schlüssel."),
    ("gewann", "Sie gewann den Preis."),
    ("wuchs", "Das Kind wuchs schnell."),
    ("zog", "Die Familie zog nach München."),
    ("bot", "Er bot ihr Hilfe an."),
    ("rief", "Sie rief ihre Mutter an."),
    ("warf", "Er warf den Ball."),
    ("aß", "Sie aß zu Mittag."),
    ("trank", "Er trank Kaffee."),
    ("saß", "Sie saß am Tisch."),
    ("stand", "Er stand am Fenster."),
    ("kannte", "Sie kannte die Stadt gut."),
    ("brachte", "Er brachte Blumen mit."),
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
    ("brach", "Er brach das Glas.", "brechen"),
    ("schloss", "Er schloss das Fenster.", "schließen"),
    ("begann", "Das Konzert begann pünktlich.", "beginnen"),
    ("verlor", "Er verlor seinen Schlüssel.", "verlieren"),
    ("gewann", "Sie gewann den Preis.", "gewinnen"),
    ("zog", "Die Familie zog nach München.", "ziehen"),
    ("rief", "Sie rief ihre Mutter an.", "rufen"),
    ("warf", "Er warf den Ball.", "werfen"),
    ("stand", "Er stand am Fenster.", "stehen"),
    ("saß", "Sie saß am Tisch.", "sitzen"),
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
    ("liest", "Er liest das Buch.", {"Person": "3", "Number": "Sing"}),
    ("kaufe", "Ich kaufe das Brot.", {"Person": "1", "Number": "Sing"}),
    ("kommen", "Wir kommen morgen.", {"Number": "Plur"}),
    ("schlief", "Er schlief tief.", {"Tense": "Past"}),
    ("sang", "Sie sang laut.", {"Tense": "Past"}),
    ("läuft", "Das Kind läuft schnell.", {"Person": "3", "Number": "Sing", "Tense": "Pres"}),
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
    ("hört", "Er hört mit dem Rauchen auf.", "aufhören"),
    ("fährt", "Er fährt morgen ab.", "abfahren"),
    ("gibt", "Sie gibt das Buch zurück.", "zurückgeben"),
    ("bringt", "Er bringt das Auto mit.", "mitbringen"),
    ("nimmt", "Sie nimmt an der Konferenz teil.", "teilnehmen"),
    ("sieht", "Er sieht sehr gut aus.", "aussehen"),
    ("läuft", "Das Programm läuft ab.", "ablaufen"),
    ("schläft", "Er schläft um zehn Uhr ein.", "einschlafen"),
    ("wacht", "Sie wacht früh auf.", "aufwachen"),
    ("zieht", "Er zieht seine Jacke aus.", "ausziehen"),
    ("trägt", "Sie trägt das Paket ein.", "eintragen"),
    ("stellt", "Er stellt das Gerät aus.", "ausstellen"),
    ("kauft", "Sie kauft im Supermarkt ein.", "einkaufen"),
]

SEPARABLE_VERB_FROM_PREFIX_CASES = [
    # (selected_prefix, context, expected_infinitive)
    ("an", "Ich ziehe mich an.", "anziehen"),
    ("auf", "Er steht jeden Morgen früh auf.", "aufstehen"),
    ("zu", "Sie macht die Tür zu.", "zumachen"),
    ("nieder", "Er legte das Buch nieder.", "niederlegen"),
    ("ab", "Der Zug fährt um acht ab.", "abfahren"),
    ("mit", "Er bringt seinen Bruder mit.", "mitbringen"),
    ("aus", "Sie zieht ihre Jacke aus.", "ausziehen"),
    ("ein", "Sie kauft im Laden ein.", "einkaufen"),
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
    ("fahren", "Sie darf alleine fahren."),
    ("schreiben", "Er soll einen Brief schreiben."),
    ("kommen", "Wir müssen pünktlich kommen."),
    ("bleiben", "Du kannst heute Nacht bleiben."),
    ("sprechen", "Er möchte laut sprechen."),
    ("kaufen", "Ich will ein Auto kaufen."),
    ("reisen", "Sie darf alleine reisen."),
    ("kochen", "Er kann gut kochen."),
    ("warten", "Wir müssen noch warten."),
    ("schlafen", "Das Kind soll jetzt schlafen."),
    ("essen", "Du darfst hier essen."),
    ("trinken", "Man sollte mehr Wasser trinken."),
]

MODAL_SELECTED_CASES = [
    # (modal_word, context) — selecting the modal itself should also yield conjugated_verb
    ("kann", "Er kann gut schwimmen."),
    ("muss", "Sie muss morgen arbeiten."),
    ("will", "Ich will ein Auto kaufen."),
    ("soll", "Er soll einen Brief schreiben."),
    ("darf", "Sie darf alleine fahren."),
    ("möchte", "Er möchte ein Buch lesen."),
    ("könnte", "Sie könnte morgen kommen."),
    ("müsste", "Er müsste früher aufstehen."),
    ("sollte", "Du solltest mehr schlafen."),
    ("wollte", "Er wollte nach Hause gehen."),
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

    @pytest.mark.parametrize(
        "word,context",
        MODAL_SELECTED_CASES,
        ids=[c[0] for c in MODAL_SELECTED_CASES],
    )
    def test_modal_selected_is_verb(self, word, context):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "conjugated_verb", (
            f"Modal '{word}' in '{context}' should be 'conjugated_verb', got '{result.word_type}'"
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
    ("helfen", "Sie versucht, ihm zu helfen."),
    ("lernen", "Er fängt an, Deutsch zu lernen."),
    ("sprechen", "Sie bat ihn, lauter zu sprechen."),
    ("kommen", "Er vergaß, rechtzeitig zu kommen."),
    ("kaufen", "Sie hat vergessen, Brot zu kaufen."),
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
    ("getrunken", "Er hat Wasser getrunken.", "Perfekt"),
    ("gekauft", "Sie hat ein Kleid gekauft.", "Perfekt"),
    ("gearbeitet", "Er hat hart gearbeitet.", "Perfekt"),
    ("gespielt", "Die Kinder haben gespielt.", "Perfekt"),
    ("gesungen", "Er hat ein Lied gesungen.", "Perfekt"),
    ("geschlafen", "Das Kind hat gut geschlafen.", "Perfekt"),
    ("geöffnet", "Sie hat die Tür geöffnet.", "Perfekt"),
    ("gefunden", "Er hat den Schlüssel gefunden.", "Perfekt"),
    ("gebracht", "Sie hat Blumen gebracht.", "Perfekt"),
    ("genommen", "Er hat das Buch genommen.", "Perfekt"),
    # Plusquamperfekt
    ("gegessen", "Ich hatte schon gegessen.", "Plusquamperfekt"),
    ("gefahren", "Wir waren nach Berlin gefahren.", "Plusquamperfekt"),
    ("geschlafen", "Als er ankam, hatte sie schon geschlafen.", "Plusquamperfekt"),
    ("gegangen", "Sie war schon gegangen, als er ankam.", "Plusquamperfekt"),
    # Futur I
    ("kommen", "Er wird morgen kommen.", "Futur"),
    ("arbeiten", "Sie wird nächste Woche arbeiten.", "Futur"),
    ("reisen", "Wir werden nach Spanien reisen.", "Futur"),
    # Passiv
    ("gebaut", "Das Haus wird gebaut.", "passiv"),
    ("repariert", "Das Auto wird repariert.", "passiv"),
    ("geöffnet", "Die Tür wird geöffnet.", "passiv"),
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
    ("Städte", "Die Städte wachsen schnell.", "Stadt"),
    ("Vögel", "Die Vögel singen.", "Vogel"),
    ("Blumen", "Die Blumen blühen.", "Blume"),
    ("Bäume", "Die Bäume sind alt.", "Baum"),
    ("Tiere", "Die Tiere schlafen.", "Tier"),
    ("Schulen", "Die Schulen sind geschlossen.", "Schule"),
    ("Züge", "Die Züge fahren pünktlich.", "Zug"),
    ("Flüsse", "Die Flüsse sind tief.", "Fluss"),
    ("Türen", "Die Türen sind offen.", "Tür"),
    ("Fenster", "Die Fenster sind geschlossen.", "Fenster"),
    ("Tische", "Die Tische sind neu.", "Tisch"),
    ("Stühle", "Die Stühle sind alt.", "Stuhl"),
    ("Briefe", "Die Briefe sind angekommen.", "Brief"),
    ("Wörter", "Die Wörter sind schwer.", "Wort"),
    ("Sätze", "Die Sätze sind lang.", "Satz"),
    ("Augen", "Ihre Augen sind blau.", "Auge"),
    ("Hände", "Seine Hände sind kalt.", "Hand"),
    ("Füße", "Meine Füße tun weh.", "Fuß"),
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
    ("Baum", "Der Baum ist alt.", "Masc"),
    ("Blume", "Die Blume ist schön.", "Fem"),
    ("Auto", "Das Auto ist neu.", "Neut"),
    ("Zug", "Der Zug kommt pünktlich.", "Masc"),
    ("Straße", "Die Straße ist lang.", "Fem"),
    ("Wasser", "Das Wasser ist kalt.", "Neut"),
    ("Lehrer", "Der Lehrer erklärt.", "Masc"),
    ("Zeitung", "Die Zeitung liegt auf dem Tisch.", "Fem"),
    ("Fenster", "Das Fenster ist offen.", "Neut"),
    ("Brief", "Der Brief ist angekommen.", "Masc"),
    ("Mutter", "Die Mutter kocht.", "Fem"),
    ("Vater", "Der Vater arbeitet.", "Masc"),
    ("Tier", "Das Tier schläft.", "Neut"),
    ("Berg", "Der Berg ist hoch.", "Masc"),
    ("Nacht", "Die Nacht ist lang.", "Fem"),
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
    ("ließ", "Er ließ das Paket liefern.", "liefern lassen"),
    ("lassen", "Wir lassen das Haus streichen.", "streichen lassen"),
    ("lässt", "Das lässt sich nicht leugnen.", "sich leugnen lassen"),
]

LASSEN_RELATED_WORDS_CASES = [
    # When selecting the main infinitive verb, lassen should appear in related words
    ("reparieren", "Sie lässt das Auto reparieren.", "lässt"),
    ("erklären", "Das lässt sich erklären.", "lässt"),
    ("liefern", "Er ließ das Paket liefern.", "ließ"),
]

LASSEN_MODAL_CLUSTER_CASES = [
    # (selected_word, context) — modal + verb + lassen cluster: all 3 should be detected
    ("lassen", "Sollte er wirklich Brücken bombardieren lassen.", "conjugated_verb"),
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

    @pytest.mark.parametrize(
        "word,context,expected_related_text",
        LASSEN_RELATED_WORDS_CASES,
        ids=[c[0] for c in LASSEN_RELATED_WORDS_CASES],
    )
    def test_lassen_from_infinitive(self, word, context, expected_related_text):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.lang_analysis is not None, (
            f"'{word}' in '{context}' should detect lassen construction"
        )
        related_texts = [r.text.lower() for r in result.lang_analysis.related]
        assert expected_related_text.lower() in related_texts, (
            f"'{word}' related should include '{expected_related_text}', got {related_texts}"
        )

    @pytest.mark.parametrize(
        "word,context,expected_word_type",
        LASSEN_MODAL_CLUSTER_CASES,
        ids=[c[0] for c in LASSEN_MODAL_CLUSTER_CASES],
    )
    def test_lassen_modal_cluster(self, word, context, expected_word_type):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == expected_word_type, (
            f"'{word}' in '{context}' should be '{expected_word_type}', got '{result.word_type}'"
        )
        assert result.lang_analysis is not None
        related_texts = [r.text.lower() for r in result.lang_analysis.related]
        assert len(related_texts) >= 1, (
            f"'{word}' should have at least 1 related word (modal or main verb), got {related_texts}"
        )


# ---------------------------------------------------------------------------
# Adjectives
# ---------------------------------------------------------------------------
ADJECTIVE_TYPE_CASES = [
    # (word, context) — should be classified as "adjective"
    ("schönen", "Das ist ein schönes Bild."),
    ("großen", "Er kaufte ein großes Haus."),
    ("kleinen", "Das kleine Kind lachte."),
    ("alten", "Der alte Mann geht spazieren."),
    ("neuen", "Sie kaufte ein neues Auto."),
    ("guten", "Das ist ein guter Plan."),
    ("langen", "Der lange Weg war anstrengend."),
    ("roten", "Sie trägt ein rotes Kleid."),
    ("schnellen", "Der schnelle Zug kam an."),
    ("interessanten", "Das war ein interessanter Vortrag."),
    ("deutschen", "Das ist ein deutsches Produkt."),
    ("wichtigen", "Das ist eine wichtige Entscheidung."),
    ("jungen", "Der junge Mann arbeitet hart."),
    ("kalten", "Das kalte Wasser erfrischt."),
    ("starken", "Er hat einen starken Willen."),
]

ADJECTIVE_LEMMA_CASES = [
    # (inflected, context, expected_lemma)
    ("schönen", "Das ist ein schönes Bild.", "schön"),
    ("großen", "Er kaufte ein großes Haus.", "groß"),
    ("kleinen", "Das kleine Kind lachte.", "klein"),
    ("alten", "Der alte Mann geht spazieren.", "alt"),
    ("neuen", "Sie kaufte ein neues Auto.", "neu"),
    ("guten", "Das ist ein guter Plan.", "gut"),
    ("roten", "Sie trägt ein rotes Kleid.", "rot"),
    ("schnellen", "Der schnelle Zug kam an.", "schnell"),
    ("jungen", "Der junge Mann arbeitet hart.", "jung"),
    ("kalten", "Das kalte Wasser erfrischt.", "kalt"),
]

ADJECTIVE_DEGREE_CASES = [
    # (word, context, expected_degree_in_breakdown)
    ("schneller", "Er ist schneller als sein Bruder.", "comparative"),
    ("älter", "Sie ist älter als ich.", "comparative"),
    ("besser", "Das ist besser als vorher.", "comparative"),
    ("größer", "Das Haus ist größer als erwartet.", "comparative"),
]


class TestAdjectives:
    """Test adjective detection, lemma resolution, and degree."""

    @pytest.mark.parametrize(
        "word,context",
        ADJECTIVE_TYPE_CASES,
        ids=[c[0] for c in ADJECTIVE_TYPE_CASES],
    )
    def test_adjective_type(self, word, context):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "adjective", (
            f"'{word}' should be 'adjective', got '{result.word_type}'"
        )

    @pytest.mark.parametrize(
        "word,context,expected_lemma",
        ADJECTIVE_LEMMA_CASES,
        ids=[c[0] for c in ADJECTIVE_LEMMA_CASES],
    )
    def test_adjective_lemma(self, word, context, expected_lemma):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.lemma == expected_lemma, (
            f"'{word}' lemma should be '{expected_lemma}', got '{result.lemma}'"
        )

    @pytest.mark.parametrize(
        "word,context,expected_degree",
        ADJECTIVE_DEGREE_CASES,
        ids=[c[0] for c in ADJECTIVE_DEGREE_CASES],
    )
    def test_adjective_comparative(self, word, context, expected_degree):
        from breakdown import generate_adjective_breakdown
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "adjective", (
            f"'{word}' should be 'adjective', got '{result.word_type}'"
        )
        breakdown = generate_adjective_breakdown(result, "test")
        assert breakdown is not None, f"'{word}' should have a breakdown"
        assert expected_degree.lower() in breakdown.lower(), (
            f"'{word}' breakdown should mention '{expected_degree}', got '{breakdown}'"
        )


# ---------------------------------------------------------------------------
# Noun case/number morphology
# ---------------------------------------------------------------------------
NOUN_CASE_CASES = [
    # (word, context, expected_case)
    ("Mann", "Ich sehe den Mann.", "Acc"),
    ("Frau", "Er hilft der Frau.", "Dat"),
    ("Kind", "Das Kind spielt.", "Nom"),
    ("Tisch", "Er steht am Tisch.", "Dat"),
    ("Buch", "Ich lese das Buch.", "Acc"),
    ("Stadt", "Er kommt aus der Stadt.", "Dat"),
    ("Hund", "Der Hund bellt.", "Nom"),
    ("Haus", "Er geht ins Haus.", "Acc"),
]

NOUN_NUMBER_CASES = [
    # (word, context, expected_number)
    ("Männer", "Die Männer arbeiten.", "Plur"),
    ("Mann", "Der Mann geht.", "Sing"),
    ("Kinder", "Die Kinder spielen.", "Plur"),
    ("Kind", "Das Kind spielt.", "Sing"),
    ("Bücher", "Die Bücher sind alt.", "Plur"),
    ("Buch", "Das Buch ist neu.", "Sing"),
    ("Städte", "Die Städte wachsen.", "Plur"),
    ("Stadt", "Die Stadt ist groß.", "Sing"),
]


class TestNounMorphology:
    """Test noun case and number detection."""

    @pytest.mark.parametrize(
        "word,context,expected_case",
        NOUN_CASE_CASES,
        ids=[c[0] for c in NOUN_CASE_CASES],
    )
    def test_noun_case(self, word, context, expected_case):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.morph.get("Case") == expected_case, (
            f"'{word}' case should be '{expected_case}', got '{result.morph.get('Case')}' "
            f"(full morph: {result.morph})"
        )

    @pytest.mark.parametrize(
        "word,context,expected_number",
        NOUN_NUMBER_CASES,
        ids=[c[0] for c in NOUN_NUMBER_CASES],
    )
    def test_noun_number(self, word, context, expected_number):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.morph.get("Number") == expected_number, (
            f"'{word}' number should be '{expected_number}', got '{result.morph.get('Number')}'"
        )


# ---------------------------------------------------------------------------
# Simple words (no special detection)
# ---------------------------------------------------------------------------
SIMPLE_WORD_CASES = [
    # (word, context) — common adverbs, conjunctions, particles: should be "simple"
    ("sehr", "Das ist sehr gut."),
    ("aber", "Er kommt, aber er ist müde."),
    ("auch", "Sie ist auch hier."),
    ("noch", "Er ist noch nicht da."),
    ("schon", "Sie ist schon gegangen."),
    ("immer", "Er ist immer pünktlich."),
    ("hier", "Ich bin hier."),
    ("dort", "Er steht dort."),
    ("heute", "Heute ist Montag."),
    ("morgen", "Wir fahren morgen ab."),
    ("vielleicht", "Vielleicht kommt er später."),
    ("wirklich", "Das ist wirklich schön."),
    ("leider", "Das geht leider nicht."),
    ("endlich", "Er ist endlich da."),
]


class TestSimpleWords:
    """Test that non-special words fall through to 'simple' classification."""

    @pytest.mark.parametrize(
        "word,context",
        SIMPLE_WORD_CASES,
        ids=[c[0] for c in SIMPLE_WORD_CASES],
    )
    def test_simple_word_type(self, word, context):
        result = analyze_word(word, context=context, source_lang="de")
        assert result.word_type == "simple", (
            f"'{word}' should be 'simple', got '{result.word_type}'"
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

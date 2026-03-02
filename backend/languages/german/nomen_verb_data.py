"""German Nomen-Verb-Verbindungen (Funktionsverbgefüge) A1–C2.

Fixed noun+verb expressions where the noun carries the meaning and the verb is
semantically light (e.g., "eine Frage stellen", "Bescheid geben").

The dictionary maps (noun, verb_lemma) → full canonical expression.
Detection matches the noun by text and the verb by lemma in the spaCy doc.
Some expressions also have a preposition (e.g., "in Betracht ziehen") —
these are stored with an optional third element in a separate dict.

Reflexive expressions (requiring "sich") are flagged in NOMEN_VERB_REFLEXIVE —
a set of (noun, verb_lemma) keys whose canonical form includes a fixed "sich".
"""

# ── (noun, verb_lemma) → canonical expression ───────────────────────────
NOMEN_VERB: dict[tuple[str, str], str] = {

    # ── A ────────────────────────────────────────────────────────────────
    ("Abschied", "nehmen"): "Abschied nehmen",
    ("Absicht", "haben"): "die Absicht haben",
    ("Abstand", "nehmen"): "Abstand nehmen",
    ("Anerkennung", "finden"): "Anerkennung finden",
    ("Angebot", "ablehnen"): "ein Angebot ablehnen",
    ("Angebot", "machen"): "ein Angebot machen",
    ("Angst", "haben"): "Angst haben",
    ("Angst", "machen"): "Angst machen",
    ("Anklage", "erheben"): "Anklage erheben",
    ("Anklang", "finden"): "Anklang finden",
    ("Anspruch", "erheben"): "Anspruch erheben",
    ("Ansprüche", "stellen"): "Ansprüche stellen",
    ("Anstrengung", "unternehmen"): "eine Anstrengung unternehmen",
    ("Anteil", "nehmen"): "Anteil nehmen",
    ("Antrag", "einreichen"): "einen Antrag einreichen",
    ("Antrag", "stellen"): "einen Antrag stellen",
    ("Antwort", "geben"): "Antwort geben",
    ("Anzeige", "erstatten"): "Anzeige erstatten",
    ("Appetit", "machen"): "Appetit machen",
    ("Arbeit", "leisten"): "Arbeit leisten",
    ("Aufgaben", "stellen"): "Aufgaben stellen",
    ("Aufsehen", "erregen"): "Aufsehen erregen",
    ("Auftrag", "ausführen"): "den Auftrag ausführen",
    ("Auftrag", "erteilen"): "einen Auftrag erteilen",
    ("Auftrag", "geben"): "den Auftrag geben",
    ("Auskunft", "erteilen"): "Auskunft erteilen",
    ("Auskunft", "geben"): "Auskunft geben",
    ("Ausnahme", "machen"): "eine Ausnahme machen",
    ("Aussage", "machen"): "eine Aussage machen",

    # ── B ────────────────────────────────────────────────────────────────
    ("Beachtung", "finden"): "Beachtung finden",
    ("Beachtung", "schenken"): "Beachtung schenken",
    ("Bedeutung", "haben"): "Bedeutung haben",
    ("Bedingung", "stellen"): "eine Bedingung stellen",
    ("Bedingungen", "annehmen"): "Bedingungen annehmen",
    ("Bedingungen", "stellen"): "Bedingungen stellen",
    ("Befehl", "ausführen"): "den Befehl ausführen",
    ("Befehl", "geben"): "den Befehl geben",
    ("Beitrag", "leisten"): "einen Beitrag leisten",
    ("Bekanntschaft", "machen"): "Bekanntschaft machen",
    ("Berechnungen", "anstellen"): "genaue Berechnungen anstellen",
    ("Beruf", "ausüben"): "einen Beruf ausüben",
    ("Berufung", "einlegen"): "Berufung einlegen",
    ("Berücksichtigung", "finden"): "Berücksichtigung finden",
    ("Bescheid", "geben"): "Bescheid geben",
    ("Bescheid", "sagen"): "Bescheid sagen",
    ("Bescheid", "wissen"): "Bescheid wissen",
    ("Beschluss", "fassen"): "einen Beschluss fassen",
    ("Beschwerde", "einlegen"): "Beschwerde einlegen",
    ("Beschwerde", "einreichen"): "Beschwerde einreichen",
    ("Besitz", "ergreifen"): "Besitz ergreifen",
    ("Besuch", "abstatten"): "einen Besuch abstatten",
    ("Besuch", "machen"): "einen Besuch machen",
    ("Beweis", "erbringen"): "einen Beweis erbringen",
    ("Beziehung", "haben"): "eine Beziehung haben",
    ("Bezug", "nehmen"): "Bezug nehmen",
    ("Beispiel", "nehmen"): "ein Beispiel nehmen",

    # ── D ────────────────────────────────────────────────────────────────
    ("Dank", "sagen"): "Dank sagen",
    ("Dienst", "antreten"): "den Dienst antreten",
    ("Dienst", "erweisen"): "einen Dienst erweisen",
    ("Drohung", "aussprechen"): "eine Drohung aussprechen",
    ("Dummheit", "begehen"): "eine Dummheit begehen",

    # ── E ────────────────────────────────────────────────────────────────
    ("Eid", "ablegen"): "einen Eid ablegen",
    ("Eindruck", "gewinnen"): "den Eindruck gewinnen",
    ("Eindruck", "hinterlassen"): "einen Eindruck hinterlassen",
    ("Eindruck", "machen"): "Eindruck machen",
    ("Einfluss", "ausüben"): "Einfluss ausüben",
    ("Einfluss", "nehmen"): "Einfluss nehmen",
    ("Einladung", "annehmen"): "die Einladung annehmen",
    ("Einwand", "erheben"): "einen Einwand erheben",
    ("Einwilligung", "geben"): "seine Einwilligung geben",
    ("Ende", "finden"): "ein Ende finden",
    ("Ende", "machen"): "ein Ende machen",
    ("Ende", "nehmen"): "ein Ende nehmen",
    ("Entdeckung", "machen"): "eine Entdeckung machen",
    ("Entscheidung", "fällen"): "eine Entscheidung fällen",
    ("Entscheidung", "treffen"): "eine Entscheidung treffen",
    ("Erfolg", "haben"): "Erfolg haben",
    ("Erfahrung", "machen"): "eine Erfahrung machen",
    ("Erinnerungen", "wecken"): "Erinnerungen wecken",
    ("Erklärung", "abgeben"): "eine Erklärung abgeben",
    ("Erkundigungen", "einziehen"): "Erkundigungen einziehen",
    ("Erlaubnis", "erteilen"): "eine Erlaubnis erteilen",
    ("Erlaubnis", "geben"): "die Erlaubnis geben",
    ("Ersatz", "leisten"): "Ersatz leisten",
    ("Erwartungen", "wecken"): "Erwartungen wecken",

    # ── F ────────────────────────────────────────────────────────────────
    ("Falle", "stellen"): "eine Falle stellen",
    ("Fehler", "begehen"): "einen Fehler begehen",
    ("Fehler", "machen"): "einen Fehler machen",
    ("Feierabend", "machen"): "Feierabend machen",
    ("Flucht", "ergreifen"): "die Flucht ergreifen",
    ("Folge", "leisten"): "Folge leisten",
    ("Forderung", "stellen"): "eine Forderung stellen",
    ("Frage", "stellen"): "eine Frage stellen",
    ("Freude", "bereiten"): "Freude bereiten",
    ("Freude", "machen"): "Freude machen",
    ("Freundschaft", "schließen"): "Freundschaft schließen",
    ("Frieden", "stiften"): "Frieden stiften",
    ("Furcht", "einflößen"): "Furcht einflößen",

    # ── G ────────────────────────────────────────────────────────────────
    ("Garantie", "geben"): "die Garantie geben",
    ("Geduld", "haben"): "Geduld haben",
    ("Gebrauch", "machen"): "Gebrauch machen",
    ("Gedanken", "machen"): "sich Gedanken machen",
    ("Gedanken", "hingeben"): "sich seinen Gedanken hingeben",
    ("Gehör", "verschaffen"): "sich Gehör verschaffen",
    ("Gelegenheit", "verschaffen"): "sich eine Gelegenheit verschaffen",
    ("Gewissheit", "verschaffen"): "sich Gewissheit verschaffen",
    ("Gefahr", "laufen"): "Gefahr laufen",
    ("Gefallen", "finden"): "Gefallen finden",
    ("Gefühl", "haben"): "ein Gefühl haben",
    ("Geheimnis", "bewahren"): "ein Geheimnis bewahren",
    ("Gelegenheit", "ergreifen"): "die Gelegenheit ergreifen",
    ("Gespräch", "führen"): "ein Gespräch führen",
    ("Geständnis", "ablegen"): "ein Geständnis ablegen",
    ("Gewicht", "legen"): "Gewicht legen",
    ("Glück", "haben"): "Glück haben",
    ("Grund", "angeben"): "einen Grund angeben",

    # ── H ────────────────────────────────────────────────────────────────
    ("Handel", "treiben"): "Handel treiben",
    ("Hilfe", "leisten"): "Hilfe leisten",
    ("Hoffnung", "aufgeben"): "die Hoffnung aufgeben",
    ("Hoffnung", "haben"): "Hoffnung haben",
    ("Hoffnung", "hegen"): "Hoffnung hegen",
    ("Hoffnung", "machen"): "Hoffnung machen",
    ("Hunger", "haben"): "Hunger haben",

    # ── I ────────────────────────────────────────────────────────────────
    ("Interesse", "haben"): "Interesse haben",
    ("Interesse", "wecken"): "Interesse wecken",

    # ── K ────────────────────────────────────────────────────────────────
    ("Kenntnis", "nehmen"): "Kenntnis nehmen",
    ("Klage", "erheben"): "eine Klage erheben",
    ("Konsequenz", "ziehen"): "die Konsequenz ziehen",
    ("Krieg", "führen"): "Krieg führen",
    ("Kritik", "üben"): "Kritik üben",
    ("Kummer", "machen"): "Kummer machen",
    ("Kummer", "zufügen"): "Kummer zufügen",
    ("Kurs", "nehmen"): "Kurs nehmen",

    # ── L ────────────────────────────────────────────────────────────────
    ("Lust", "haben"): "Lust haben",

    # ── M ────────────────────────────────────────────────────────────────
    ("Maßnahmen", "ergreifen"): "Maßnahmen ergreifen",
    ("Maßnahmen", "treffen"): "Maßnahmen treffen",
    ("Meinung", "bilden"): "sich eine Meinung bilden",
    ("Missbrauch", "treiben"): "Missbrauch treiben",
    ("Mord", "begehen"): "einen Mord begehen",
    ("Mord", "verüben"): "einen Mord verüben",
    ("Mut", "fassen"): "Mut fassen",
    ("Mut", "machen"): "Mut machen",
    ("Mühe", "geben"): "sich Mühe geben",
    ("Mühe", "machen"): "Mühe machen",

    # ── N ────────────────────────────────────────────────────────────────
    ("Nachforschungen", "anstellen"): "Nachforschungen anstellen",
    ("Nachricht", "geben"): "Nachricht geben",
    ("Nachsicht", "üben"): "Nachsicht üben",
    ("Neugier", "wecken"): "Neugier wecken",
    ("Niederlage", "erleiden"): "eine Niederlage erleiden",
    ("Niederlage", "zufügen"): "eine Niederlage zufügen",
    ("Notiz", "nehmen"): "Notiz nehmen",

    # ── P ────────────────────────────────────────────────────────────────
    ("Partei", "ergreifen"): "Partei ergreifen",
    ("Pause", "machen"): "Pause machen",
    ("Platz", "nehmen"): "Platz nehmen",
    ("Protest", "einlegen"): "Protest einlegen",
    ("Protest", "erheben"): "Protest erheben",
    ("Prüfung", "ablegen"): "eine Prüfung ablegen",
    ("Prüfung", "bestehen"): "eine Prüfung bestehen",

    # ── R ────────────────────────────────────────────────────────────────
    ("Rache", "nehmen"): "Rache nehmen",
    ("Rat", "geben"): "Rat geben",
    ("Rat", "holen"): "sich Rat holen",
    ("Rechenschaft", "ablegen"): "Rechenschaft ablegen",
    ("Recht", "haben"): "Recht haben",
    ("Rede", "halten"): "eine Rede halten",
    ("Reise", "machen"): "eine Reise machen",
    ("Rolle", "spielen"): "eine Rolle spielen",
    ("Rücksicht", "nehmen"): "Rücksicht nehmen",
    ("Ruhe", "bewahren"): "Ruhe bewahren",

    # ── S ────────────────────────────────────────────────────────────────
    ("Schaden", "anrichten"): "Schaden anrichten",
    ("Schaden", "zufügen"): "Schaden zufügen",
    ("Schluss", "machen"): "Schluss machen",
    ("Schuld", "haben"): "Schuld haben",
    ("Schutz", "bieten"): "Schutz bieten",
    ("Selbstmord", "begehen"): "Selbstmord begehen",
    ("Sorge", "tragen"): "Sorge tragen",
    ("Sorgen", "machen"): "sich Sorgen machen",
    ("Spaß", "gönnen"): "sich einen Spaß gönnen",
    ("Spaß", "machen"): "Spaß machen",
    ("Sport", "treiben"): "Sport treiben",
    ("Stellung", "nehmen"): "Stellung nehmen",
    ("Strafe", "verhängen"): "Strafe verhängen",
    ("Streit", "führen"): "einen Streit führen",

    # ── T ────────────────────────────────────────────────────────────────
    ("Ton", "angeben"): "den Ton angeben",

    # ── U ────────────────────────────────────────────────────────────────
    ("Überblick", "verschaffen"): "sich einen Überblick verschaffen",
    ("Ultimatum", "stellen"): "ein Ultimatum stellen",
    ("Unfug", "anstellen"): "Unfug anstellen",
    ("Unfug", "treiben"): "Unfug treiben",
    ("Unfrieden", "stiften"): "Unfrieden stiften",
    ("Unheil", "anrichten"): "Unheil anrichten",
    ("Unrecht", "haben"): "Unrecht haben",
    ("Unterhaltung", "führen"): "eine Unterhaltung führen",
    ("Unterricht", "geben"): "Unterricht geben",
    ("Unterstützung", "finden"): "Unterstützung finden",
    ("Urlaub", "machen"): "Urlaub machen",
    ("Urteil", "fällen"): "ein Urteil fällen",
    ("Überlegungen", "anstellen"): "Überlegungen anstellen",
    ("Überzeugung", "gewinnen"): "die Überzeugung gewinnen",

    # ── V ────────────────────────────────────────────────────────────────
    ("Verantwortung", "tragen"): "Verantwortung tragen",
    ("Verdienste", "erwerben"): "sich Verdienste erwerben",
    ("Verantwortung", "übernehmen"): "Verantwortung übernehmen",
    ("Verbrechen", "begehen"): "ein Verbrechen begehen",
    ("Verbrechen", "verüben"): "ein Verbrechen verüben",
    ("Vereinbarung", "treffen"): "eine Vereinbarung treffen",
    ("Verrat", "begehen"): "Verrat begehen",
    ("Versprechen", "geben"): "sein Versprechen geben",
    ("Versprechen", "halten"): "sein Versprechen halten",
    ("Verständnis", "haben"): "Verständnis haben",
    ("Vertrauen", "haben"): "Vertrauen haben",
    ("Vertrauen", "schenken"): "Vertrauen schenken",
    ("Vertrag", "abschließen"): "einen Vertrag abschließen",
    ("Verwendung", "finden"): "Verwendung finden",
    ("Versuch", "machen"): "einen Versuch machen",
    ("Versuch", "unternehmen"): "einen Versuch unternehmen",
    ("Versuche", "anstellen"): "Versuche anstellen",
    ("Vorbereitungen", "treffen"): "Vorbereitungen treffen",
    ("Vorlesung", "halten"): "eine Vorlesung halten",
    ("Vorschlag", "einreichen"): "einen Vorschlag einreichen",
    ("Vorschlag", "machen"): "einen Vorschlag machen",
    ("Vorteil", "haben"): "einen Vorteil haben",
    ("Vortrag", "halten"): "einen Vortrag halten",

    # ── W ────────────────────────────────────────────────────────────────
    ("Wahl", "treffen"): "eine Wahl treffen",
    ("Wert", "legen"): "Wert legen",
    ("Widerstand", "aufgeben"): "Widerstand aufgeben",
    ("Widerstand", "leisten"): "Widerstand leisten",
    ("Wort", "ergreifen"): "das Wort ergreifen",
    ("Wort", "halten"): "sein Wort halten",
    ("Wunder", "wirken"): "Wunder wirken",
    ("Wunsch", "erfüllen"): "einen Wunsch erfüllen",

    # ── Z ────────────────────────────────────────────────────────────────
    ("Zeit", "haben"): "Zeit haben",
    ("Zivildienst", "leisten"): "Zivildienst leisten",
    ("Zugang", "haben"): "Zugang haben",
    ("Zurückhaltung", "üben"): "Zurückhaltung üben",
    ("Zusammenhang", "herstellen"): "einen Zusammenhang herstellen",
    ("Zusicherung", "geben"): "die Zusicherung geben",
    ("Zuspruch", "finden"): "Zuspruch finden",
    ("Zustimmung", "geben"): "Zustimmung geben",
    ("Zweifel", "haben"): "Zweifel haben",
}

# ── prep + noun + verb_lemma → canonical expression ─────────────────────
# For Nomen-Verb-Verbindungen with a fixed preposition
NOMEN_VERB_PREP: dict[tuple[str, str, str], str] = {

    # ── an + Noun + Verb ─────────────────────────────────────────────────
    ("an", "Arbeit", "gehen"): "an die Arbeit gehen",

    # ── in + Noun + Verb ─────────────────────────────────────────────────
    ("in", "Angriff", "nehmen"): "in Angriff nehmen",
    ("in", "Anspruch", "nehmen"): "in Anspruch nehmen",
    ("in", "Augenschein", "nehmen"): "in Augenschein nehmen",
    ("in", "Aussicht", "stellen"): "in Aussicht stellen",
    ("in", "Besitz", "nehmen"): "in Besitz nehmen",
    ("in", "Betracht", "ziehen"): "in Betracht ziehen",
    ("in", "Betrieb", "nehmen"): "in Betrieb nehmen",
    ("in", "Betrieb", "setzen"): "in Betrieb setzen",
    ("in", "Brand", "geraten"): "in Brand geraten",
    ("in", "Brand", "setzen"): "in Brand setzen",
    ("in", "Brand", "stecken"): "in Brand stecken",
    ("in", "Empfang", "nehmen"): "in Empfang nehmen",
    ("in", "Erfahrung", "bringen"): "in Erfahrung bringen",
    ("in", "Erfüllung", "gehen"): "in Erfüllung gehen",
    ("in", "Erstaunen", "setzen"): "in Erstaunen setzen",
    ("in", "Erstaunen", "versetzen"): "in Erstaunen versetzen",
    ("in", "Erwägung", "ziehen"): "in Erwägung ziehen",
    ("in", "Frage", "kommen"): "in Frage kommen",
    ("in", "Frage", "stellen"): "in Frage stellen",
    ("in", "Gang", "bringen"): "in Gang bringen",
    ("in", "Gang", "kommen"): "in Gang kommen",
    ("in", "Gang", "setzen"): "in Gang setzen",
    ("in", "Gefahr", "geraten"): "in Gefahr geraten",
    ("in", "Kauf", "nehmen"): "in Kauf nehmen",
    ("in", "Kenntnis", "setzen"): "in Kenntnis setzen",
    ("in", "Kraft", "setzen"): "in Kraft setzen",
    ("in", "Kraft", "treten"): "in Kraft treten",
    ("in", "Mode", "kommen"): "in Mode kommen",
    ("in", "Ordnung", "bringen"): "in Ordnung bringen",
    ("in", "Ruhe", "lassen"): "in Ruhe lassen",
    ("in", "Schutz", "nehmen"): "in Schutz nehmen",
    ("in", "Schwierigkeiten", "geraten"): "in Schwierigkeiten geraten",
    ("in", "Verdacht", "geraten"): "in Verdacht geraten",
    ("in", "Verbindung", "bringen"): "in Verbindung bringen",
    ("in", "Verbindung", "setzen"): "in Verbindung setzen",
    ("in", "Verbindung", "stehen"): "in Verbindung stehen",
    ("in", "Vergessenheit", "geraten"): "in Vergessenheit geraten",
    ("in", "Verlegenheit", "bringen"): "in Verlegenheit bringen",
    ("in", "Verzug", "geraten"): "in Verzug geraten",

    # ── zu + Noun + Verb (zum/zur) ───────────────────────────────────────
    ("zu", "Abschluss", "bringen"): "zum Abschluss bringen",
    ("zu", "Abschluss", "kommen"): "zum Abschluss kommen",
    ("zu", "Ausdruck", "bringen"): "zum Ausdruck bringen",
    ("zu", "Ausdruck", "kommen"): "zum Ausdruck kommen",
    ("zu", "Diskussion", "stehen"): "zur Diskussion stehen",
    ("zu", "Diskussion", "stellen"): "zur Diskussion stellen",
    ("zu", "Einsatz", "bringen"): "zum Einsatz bringen",
    ("zu", "Einsatz", "kommen"): "zum Einsatz kommen",
    ("zu", "Einsicht", "bringen"): "zur Einsicht bringen",
    ("zu", "Einsicht", "kommen"): "zur Einsicht kommen",
    ("zu", "Ende", "bringen"): "zu Ende bringen",
    ("zu", "Entschluss", "kommen"): "zu dem Entschluss kommen",
    ("zu", "Ergebnis", "kommen"): "zum Ergebnis kommen",
    ("zu", "Erliegen", "bringen"): "zum Erliegen bringen",
    ("zu", "Erliegen", "kommen"): "zum Erliegen kommen",
    ("zu", "Folge", "haben"): "zur Folge haben",
    ("zu", "Kenntnis", "nehmen"): "zur Kenntnis nehmen",
    ("zu", "Lachen", "bringen"): "zum Lachen bringen",
    ("zu", "Last", "fallen"): "zur Last fallen",
    ("zu", "Rechenschaft", "ziehen"): "zur Rechenschaft ziehen",
    ("zu", "Ruhe", "kommen"): "zur Ruhe kommen",
    ("zu", "Sprache", "bringen"): "zur Sprache bringen",
    ("zu", "Sprache", "kommen"): "zur Sprache kommen",
    ("zu", "Stillstand", "bringen"): "zum Stillstand bringen",
    ("zu", "Stillstand", "kommen"): "zum Stillstand kommen",
    ("zu", "Überzeugung", "gelangen"): "zu der Überzeugung gelangen",
    ("zu", "Verantwortung", "ziehen"): "zur Verantwortung ziehen",
    ("zu", "Verfügung", "stehen"): "zur Verfügung stehen",
    ("zu", "Verfügung", "stellen"): "zur Verfügung stellen",
    ("zu", "Vernunft", "bringen"): "zur Vernunft bringen",
    ("zu", "Vernunft", "gelangen"): "zur Vernunft gelangen",
    ("zu", "Vernunft", "kommen"): "zur Vernunft kommen",
    ("zu", "Vorschein", "bringen"): "zum Vorschein bringen",
    ("zu", "Vorschein", "kommen"): "zum Vorschein kommen",
    ("zu", "Wahl", "stehen"): "zur Wahl stehen",
    ("zu", "Weinen", "bringen"): "zum Weinen bringen",
    ("zu", "Wort", "kommen"): "zu Wort kommen",

    # ── auf + Noun + Verb ────────────────────────────────────────────────
    ("auf", "Ablehnung", "stoßen"): "auf Ablehnung stoßen",
    ("auf", "Kritik", "stoßen"): "auf Kritik stoßen",
    ("auf", "Nerven", "gehen"): "auf die Nerven gehen",
    ("auf", "Palme", "bringen"): "auf die Palme bringen",
    ("auf", "Probe", "stellen"): "auf die Probe stellen",

    # ── unter + Noun + Verb ──────────────────────────────────────────────
    ("unter", "Beweis", "stellen"): "unter Beweis stellen",
    ("unter", "Druck", "setzen"): "unter Druck setzen",
    ("unter", "Druck", "stehen"): "unter Druck stehen",
    ("unter", "Kontrolle", "bringen"): "unter Kontrolle bringen",
    ("unter", "Strafe", "stehen"): "unter Strafe stehen",
    ("unter", "Verdacht", "stehen"): "unter Verdacht stehen",

    # ── außer + Noun + Verb ──────────────────────────────────────────────
    ("außer", "Acht", "lassen"): "außer Acht lassen",
    ("außer", "Betrieb", "setzen"): "außer Betrieb setzen",
    ("außer", "Frage", "stehen"): "außer Frage stehen",
    ("außer", "Kontrolle", "geraten"): "außer Kontrolle geraten",
    ("außer", "Kraft", "setzen"): "außer Kraft setzen",
}

# ── Reflexive prep + noun + verb expressions (require "sich") ────────────
NOMEN_VERB_PREP_REFLEXIVE: dict[tuple[str, str, str], str] = {
    # ── in + Noun + Verb ─────────────────────────────────────────────────
    ("in", "Acht", "nehmen"): "sich in Acht nehmen",
    ("in", "Erinnerung", "rufen"): "sich etwas in Erinnerung rufen",
    ("in", "Sicherheit", "wiegen"): "sich in Sicherheit wiegen",
    ("in", "Widerspruch", "begeben"): "sich in Widerspruch begeben",

    # ── zu + Noun + Verb ─────────────────────────────────────────────────
    ("zu", "Wort", "melden"): "sich zu Wort melden",
    ("zu", "Ruhe", "setzen"): "sich zur Ruhe setzen",
    ("zu", "Recht", "finden"): "sich zurechtfinden",

    # ── auf + Noun + Verb ────────────────────────────────────────────────
    ("auf", "Kosten", "lustig machen"): "sich auf Kosten anderer lustig machen",

    # ── um + Noun + Verb ─────────────────────────────────────────────────
    ("um", "Erlaubnis", "bitten"): "sich um Erlaubnis bitten",

    # ── mit + Noun + Verb ────────────────────────────────────────────────
    ("mit", "Gedanken", "tragen"): "sich mit dem Gedanken tragen",
}

# ── Set of (noun, verb_lemma) keys that require reflexive "sich" ──────────
# These are entries in NOMEN_VERB whose canonical form begins with "sich".
NOMEN_VERB_REFLEXIVE: set[tuple[str, str]] = {
    key for key, val in NOMEN_VERB.items() if val.startswith("sich ")
}

# ── Set of (prep, noun, verb_lemma) keys that require reflexive "sich" ────
NOMEN_VERB_PREP_REFLEXIVE_KEYS: set[tuple[str, str, str]] = set(
    NOMEN_VERB_PREP_REFLEXIVE
)

# ── Reverse index: noun (lowercased) → list of (noun, verb_lemma) tuples ──
NOMEN_VERB_INDEX: dict[str, list[tuple[str, str]]] = {}
for _nv_tuple in NOMEN_VERB:
    _noun = _nv_tuple[0]
    NOMEN_VERB_INDEX.setdefault(_noun.lower(), []).append(_nv_tuple)

# ── Reverse index for prep expressions: noun (lowercased) → list of (prep, noun, verb) tuples ──
NOMEN_VERB_PREP_INDEX: dict[str, list[tuple[str, str, str]]] = {}
for _nvp_tuple in NOMEN_VERB_PREP:
    _noun_nvp = _nvp_tuple[1]  # noun is the second element
    NOMEN_VERB_PREP_INDEX.setdefault(_noun_nvp.lower(), []).append(_nvp_tuple)

# ── Reverse index for reflexive prep expressions ──────────────────────────
NOMEN_VERB_PREP_REFLEXIVE_INDEX: dict[str, list[tuple[str, str, str]]] = {}
for _nvpr_tuple in NOMEN_VERB_PREP_REFLEXIVE:
    _noun_nvpr = _nvpr_tuple[1]
    NOMEN_VERB_PREP_REFLEXIVE_INDEX.setdefault(_noun_nvpr.lower(), []).append(_nvpr_tuple)

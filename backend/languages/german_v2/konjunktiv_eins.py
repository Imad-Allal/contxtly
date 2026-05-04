"""V2 Konjunktiv I (indirekte Rede) detection.

Konjunktiv I appears mostly in news German for reported speech:
    "Er sagt, sie habe den Brief geschrieben."
    "Der Minister erklärte, das Gesetz sei wichtig."

Distinguishing features:
  - 3rd-person singular adds -e to the stem ("er sage", "er habe", "er sei")
  - For most verbs, only 3rd-person singular and 2nd-person plural are
    morphologically distinct from indicative
  - For "sein", all forms are distinct ("ich sei", "du seiest", "er sei", …)

We detect by:
  1. spaCy Mood=Sub on a present-tense verb (skip Konj II which is past)
  2. OR specific high-frequency Konj I forms ("sei", "habe", "werde",
     "könne", "müsse", "wolle", "solle", "dürfe", "möge")

This is morphology-only — no DB data needed.
"""

from dataclasses import dataclass

import simplemma
import spacy


@dataclass
class KonjunktivIInfo:
    """Detected Konjunktiv I verb form."""
    surface: str
    surface_idx: int
    lemma: str
    person: str        # '1' / '2' / '3' / ''
    number: str        # 'Sing' / 'Plur' / ''


# High-frequency Konj I forms that are unambiguous (would never be
# confused with indicative). Used as a fallback when spaCy doesn't tag
# Mood=Sub explicitly.
_KONJ_I_FORMS = {
    # sein
    "sei", "seist", "seiest", "seien", "seiet",
    # haben
    "habe", "habest", "haben", "habet",
    # werden
    "werde", "werdest", "werden", "werdet",
    # modal verbs
    "könne", "könnest", "können", "könnet",
    "müsse", "müssest", "müssen", "müsset",
    "wolle", "wollest", "wollen", "wollet",
    "solle", "sollest", "sollen", "sollet",
    "dürfe", "dürfest", "dürfen", "dürfet",
    "möge", "mögest", "mögen", "möget",
    # mögen / können — already covered above
}


def _is_konjunktiv_eins(token) -> bool:
    """Decide whether a verb token is in Konjunktiv I (present subjunctive)."""
    if token.pos_ not in ("VERB", "AUX"):
        return False

    surface = token.text.lower()

    mood = token.morph.get("Mood") or []
    tense = token.morph.get("Tense") or []

    # Konj I is morphologically subjunctive AND present (Konj II is past)
    if "Sub" in mood and "Pres" in tense:
        return True

    # Fallback: high-frequency Konj I forms (works even when spaCy
    # doesn't mark Mood=Sub explicitly)
    if surface in _KONJ_I_FORMS:
        # Avoid false-positives: "haben" / "können" etc. are also indicative
        # 1st-person plural. Require either Mood=Sub OR the form to be one
        # that's *only* Konj I (sei, habest, …)
        unambiguous = surface in {
            "sei", "seist", "seiest", "seiet",
            "habest", "habet",
            "werdest", "werdet",
            "könnest", "könnet",
            "müsse", "müssest", "müsset",
            "wolle", "wollest", "wollet",
            "solle", "sollest", "sollet",
            "dürfe", "dürfest", "dürfet",
            "möge", "mögest", "möget",
            "habe",  # 1sg pres ind too, but Konj I is the dominant news-German use
            "werde",
        }
        return unambiguous

    return False


def detect_konjunktiv_eins(target, doc: spacy.tokens.Doc) -> KonjunktivIInfo | None:
    if not _is_konjunktiv_eins(target):
        return None

    lemma = simplemma.lemmatize(target.text.lower(), lang="de") or target.lemma_ or target.text
    person_list = target.morph.get("Person") or []
    number_list = target.morph.get("Number") or []
    return KonjunktivIInfo(
        surface=target.text,
        surface_idx=target.idx,
        lemma=lemma.lower(),
        person=person_list[0] if person_list else "",
        number=number_list[0] if number_list else "",
    )

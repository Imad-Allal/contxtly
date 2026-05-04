"""V2 Zustandspassiv detection.

Distinguishes "sein + Partizip II" as a STATE (Zustandspassiv) from:
  - Vorgangspassiv (werden + Partizip II) — handled separately by v1
  - Perfekt of intransitive sein-verbs ("er ist gegangen") — different reading

  "Die Tür ist geschlossen."          → Zustandspassiv (state: door is closed)
  "Er ist gegangen."                  → Perfekt (action: he has gone)
  "Die Tür wird geschlossen."         → Vorgangspassiv (action: door is being closed)

Rule: sein + Partizip II is Zustandspassiv when the verb is *transitive*
(takes a direct object in active voice). For intransitive sein-verbs
(gehen, fahren, kommen, …), it's Perfekt.

Without a transitivity table, we use a curated list of common
intransitive sein-verbs as the negative filter — anything outside the
list with sein + Part II is treated as Zustandspassiv.

Lower confidence than v1's compound_tense detector so the Perfekt
reading wins for known intransitive sein-verbs by default; this
detector adds Zustandspassiv as the alternative reading for transitive
cases the Perfekt detector would have mislabeled.
"""

from dataclasses import dataclass

import simplemma
import spacy
from models import TokenRef


# Common German verbs that take "sein" in Perfekt (intransitive, motion,
# state-change). Used as a negative filter — sein + their Partizip II is
# Perfekt, not Zustandspassiv.
_SEIN_AUX_INTRANSITIVE = {
    "gehen", "kommen", "fahren", "reisen", "fliegen", "laufen", "rennen",
    "springen", "klettern", "schwimmen", "wandern", "segeln", "ziehen",
    "steigen", "fallen", "stürzen", "sinken", "platzen", "explodieren",
    "passieren", "geschehen", "vorkommen", "erscheinen", "verschwinden",
    "aufstehen", "einschlafen", "aufwachen", "wachsen", "sterben",
    "werden", "bleiben", "sein", "gelingen", "misslingen", "scheitern",
    "ankommen", "abreisen", "wegfahren", "weggehen", "zurückkommen",
    "verreisen", "umsteigen", "umziehen", "fortgehen", "fortfahren",
    "zerbrechen", "ertrinken", "verbluten",
}


@dataclass
class ZustandspassivInfo:
    """Detected sein + Partizip II as a state."""
    sein_text: str             # 'ist' / 'sind' / 'war' / 'waren' / …
    sein_idx: int
    participle: str            # 'geschlossen' / 'geöffnet' / …
    participle_idx: int
    verb_lemma: str            # 'schließen' / 'öffnen' / …


def _find_sein(doc: spacy.tokens.Doc, target):
    """Return the closest finite 'sein' in the same sentence, or None."""
    sent = target.sent if target.sent is not None else doc
    for t in sent:
        if t.lemma_ == "sein" and t.pos_ in ("AUX", "VERB"):
            return t
    return None


def _find_participle(doc: spacy.tokens.Doc, target):
    """Return the Partizip II in the same sentence, or None."""
    sent = target.sent if target.sent is not None else doc
    for t in sent:
        if "Part" in (t.morph.get("VerbForm") or []):
            return t
        # spaCy sometimes emits ADJ for Partizip II in predicative position
        if t.tag_ == "VVPP":
            return t
    return None


def detect_zustandspassiv(target, doc: spacy.tokens.Doc) -> ZustandspassivInfo | None:
    """Detect sein + Partizip II as Zustandspassiv.

    Selection points:
      - the sein form ('ist', 'sind', …)
      - the past participle
    """
    if target.pos_ not in ("AUX", "VERB", "ADJ"):
        return None

    sein_token = None
    part_token = None

    if target.lemma_ == "sein" and target.pos_ in ("AUX", "VERB"):
        sein_token = target
        part_token = _find_participle(doc, target)
    elif ("Part" in (target.morph.get("VerbForm") or [])
          or target.tag_ == "VVPP"
          or (target.pos_ == "ADJ" and target.dep_ == "oc")):
        part_token = target
        sein_token = _find_sein(doc, target)

    if sein_token is None or part_token is None:
        return None
    if sein_token.i == part_token.i:
        return None

    # Get the underlying verb lemma. Prefer spaCy's lemma_ (which correctly
    # handles past participles like "gefahren" → "fahren"), then fall back
    # to simplemma which often leaves participles unchanged.
    if part_token.lemma_ and part_token.lemma_ != part_token.text:
        verb_lemma = part_token.lemma_.lower()
    else:
        verb_lemma = (simplemma.lemmatize(part_token.text.lower(), lang="de")
                      or part_token.text).lower()

    # Negative filter: known intransitive sein-verbs → Perfekt, not Zustandspassiv
    if verb_lemma in _SEIN_AUX_INTRANSITIVE:
        return None

    return ZustandspassivInfo(
        sein_text=sein_token.text,
        sein_idx=sein_token.idx,
        participle=part_token.text,
        participle_idx=part_token.idx,
        verb_lemma=verb_lemma,
    )

"""V2 NVV detection: lemma-first noun matching.

V1 keys NVV entries on the noun's surface text, so plurals and
case-marked forms miss:
    "Sie stellt eine Frage."   → matches  ("Frage", "stellen")
    "Sie stellt viele Fragen." → MISSES   ("Frage", "stellen")

V2 tries the noun's lemma first, then falls back to the surface text
to preserve every v1 match. Net effect is a strict superset of v1
detection.

Everything else (reflexive handling, prep+noun+verb shape, sich
detection) is identical to v1 — only the noun key derivation changes.
"""

from dataclasses import dataclass

import spacy
from models import TokenRef
from languages.german.verbs import REFLEXIVE_PRONOUNS
from languages.german.dict_store import (
    NOMEN_VERB, NOMEN_VERB_INDEX,
    NOMEN_VERB_PREP, NOMEN_VERB_PREP_INDEX,
    NOMEN_VERB_REFLEXIVE,
    NOMEN_VERB_PREP_REFLEXIVE, NOMEN_VERB_PREP_REFLEXIVE_INDEX,
)


@dataclass
class NomenVerbInfo:
    """Detected Nomen-Verb-Verbindung (e.g., "eine Frage stellen")."""
    expression: str         # canonical form: "eine Frage stellen"
    related: list[TokenRef] # all parts except the selected word


def _noun_keys(noun_token) -> list[str]:
    """Candidate dict-key forms to try for this noun, lemma first.

    German noun lemmas are capitalised in the dicts ("Frage", "Hund").
    spaCy's lemma_ for plurals like "Fragen" returns "Frage", which is
    what we want. We dedupe and keep the surface as a fallback in case
    spaCy's lemmatiser gives a wrong answer.
    """
    out: list[str] = []
    lemma = (noun_token.lemma_ or "").strip()
    text = noun_token.text
    if lemma and lemma != text:
        out.append(lemma)
    out.append(text)
    return out


def detect_nomen_verb(target, doc: spacy.tokens.Doc) -> NomenVerbInfo | None:
    """Detect Nomen-Verb-Verbindungen from context (lemma-first matching)."""
    if target.pos_ == "NOUN":
        return _match_from_noun(target, doc)
    elif target.pos_ == "VERB":
        return _match_from_verb(target, doc)
    elif target.text.lower() in REFLEXIVE_PRONOUNS:
        return _match_from_sich(target, doc)
    return None


def _match_from_noun(noun_token, doc: spacy.tokens.Doc) -> NomenVerbInfo | None:
    """User selected the noun — find a matching verb in the sentence."""
    sich_token = _find_sich(doc)

    for noun_key in _noun_keys(noun_token):
        noun_lower = noun_key.lower()

        # 1) Reflexive prep + noun + verb (longest match, highest priority)
        if sich_token and NOMEN_VERB_PREP_REFLEXIVE_INDEX.get(noun_lower):
            verb_tokens = [t for t in doc if t.pos_ == "VERB"]
            prep_tokens = [t for t in doc if t.pos_ == "ADP"]
            for prep_t in prep_tokens:
                prep_lemma = prep_t.lemma_.lower()
                for verb_t in verb_tokens:
                    verb_lemma = verb_t.lemma_.lower()
                    key = (prep_lemma, noun_key, verb_lemma)
                    if key in NOMEN_VERB_PREP_REFLEXIVE:
                        pattern = NOMEN_VERB_PREP_REFLEXIVE[key]
                        related = [
                            TokenRef(t.text, t.idx)
                            for t in (sich_token, prep_t, verb_t)
                            if t != noun_token
                        ]
                        return NomenVerbInfo(pattern, related)

        # 2) Non-reflexive prep + noun + verb
        if NOMEN_VERB_PREP_INDEX.get(noun_lower):
            verb_tokens = [t for t in doc if t.pos_ == "VERB"]
            prep_tokens = [t for t in doc if t.pos_ == "ADP"]
            for prep_t in prep_tokens:
                prep_lemma = prep_t.lemma_.lower()
                for verb_t in verb_tokens:
                    verb_lemma = verb_t.lemma_.lower()
                    key = (prep_lemma, noun_key, verb_lemma)
                    if key in NOMEN_VERB_PREP:
                        pattern = NOMEN_VERB_PREP[key]
                        related = [
                            TokenRef(t.text, t.idx)
                            for t in (prep_t, verb_t)
                            if t != noun_token
                        ]
                        return NomenVerbInfo(pattern, related)

        # 3) Simple noun + verb (with or without sich)
        if not NOMEN_VERB_INDEX.get(noun_lower):
            continue

        for verb_t in doc:
            if verb_t.pos_ != "VERB":
                continue
            verb_lemma = verb_t.lemma_.lower()
            key = (noun_key, verb_lemma)
            if key in NOMEN_VERB:
                is_reflexive = key in NOMEN_VERB_REFLEXIVE
                if is_reflexive and not sich_token:
                    continue
                pattern = NOMEN_VERB[key]
                related_tokens = [verb_t]
                if is_reflexive and sich_token:
                    related_tokens.append(sich_token)
                related = [TokenRef(t.text, t.idx) for t in related_tokens]
                return NomenVerbInfo(pattern, related)

    return None


def _match_from_verb(verb_token, doc: spacy.tokens.Doc) -> NomenVerbInfo | None:
    """User selected the verb — find a matching noun in the sentence."""
    verb_lemma = verb_token.lemma_.lower()
    sich_token = _find_sich(doc)

    noun_tokens = [t for t in doc if t.pos_ == "NOUN"]
    if not noun_tokens:
        return None

    prep_tokens = [t for t in doc if t.pos_ == "ADP"]

    # 1) Reflexive prep + noun + verb
    if sich_token:
        for noun_t in noun_tokens:
            for noun_key in _noun_keys(noun_t):
                for prep_t in prep_tokens:
                    prep_lemma = prep_t.lemma_.lower()
                    key = (prep_lemma, noun_key, verb_lemma)
                    if key in NOMEN_VERB_PREP_REFLEXIVE:
                        pattern = NOMEN_VERB_PREP_REFLEXIVE[key]
                        related = [
                            TokenRef(t.text, t.idx)
                            for t in (sich_token, prep_t, noun_t)
                            if t != verb_token
                        ]
                        return NomenVerbInfo(pattern, related)

    # 2) Non-reflexive prep + noun + verb
    for noun_t in noun_tokens:
        for noun_key in _noun_keys(noun_t):
            for prep_t in prep_tokens:
                prep_lemma = prep_t.lemma_.lower()
                key = (prep_lemma, noun_key, verb_lemma)
                if key in NOMEN_VERB_PREP:
                    pattern = NOMEN_VERB_PREP[key]
                    related = [
                        TokenRef(t.text, t.idx)
                        for t in (prep_t, noun_t)
                        if t != verb_token
                    ]
                    return NomenVerbInfo(pattern, related)

    # 3) Simple noun + verb (with or without sich)
    for noun_t in noun_tokens:
        for noun_key in _noun_keys(noun_t):
            key = (noun_key, verb_lemma)
            if key in NOMEN_VERB:
                is_reflexive = key in NOMEN_VERB_REFLEXIVE
                if is_reflexive and not sich_token:
                    continue
                pattern = NOMEN_VERB[key]
                related_tokens = [noun_t]
                if is_reflexive and sich_token:
                    related_tokens.append(sich_token)
                related = [TokenRef(t.text, t.idx) for t in related_tokens]
                return NomenVerbInfo(pattern, related)

    return None


def _find_sich(doc: spacy.tokens.Doc):
    """Return the reflexive pronoun token if present, else None."""
    for t in doc:
        if t.text.lower() in REFLEXIVE_PRONOUNS:
            return t
    return None


def _match_from_sich(sich_token, doc: spacy.tokens.Doc) -> NomenVerbInfo | None:
    """User selected 'sich' — find a matching reflexive NVV in context."""
    verb_tokens = [t for t in doc if t.pos_ == "VERB"]
    noun_tokens = [t for t in doc if t.pos_ == "NOUN"]
    prep_tokens = [t for t in doc if t.pos_ == "ADP"]

    # 1) Reflexive prep + noun + verb
    for noun_t in noun_tokens:
        for noun_key in _noun_keys(noun_t):
            for prep_t in prep_tokens:
                prep_lemma = prep_t.lemma_.lower()
                for verb_t in verb_tokens:
                    verb_lemma = verb_t.lemma_.lower()
                    key = (prep_lemma, noun_key, verb_lemma)
                    if key in NOMEN_VERB_PREP_REFLEXIVE:
                        pattern = NOMEN_VERB_PREP_REFLEXIVE[key]
                        related = [
                            TokenRef(t.text, t.idx)
                            for t in (prep_t, noun_t, verb_t)
                            if t != sich_token
                        ]
                        return NomenVerbInfo(pattern, related)

    # 2) Simple reflexive noun + verb
    for noun_t in noun_tokens:
        for noun_key in _noun_keys(noun_t):
            for verb_t in verb_tokens:
                key = (noun_key, verb_t.lemma_.lower())
                if key in NOMEN_VERB_REFLEXIVE:
                    pattern = NOMEN_VERB[key]
                    related = [
                        TokenRef(t.text, t.idx)
                        for t in (noun_t, verb_t)
                        if t != sich_token
                    ]
                    return NomenVerbInfo(pattern, related)

    return None

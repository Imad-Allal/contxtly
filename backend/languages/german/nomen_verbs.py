"""German Nomen-Verb-Verbindungen detection."""

from dataclasses import dataclass

import spacy
from models import TokenRef
from languages.german.nomen_verb_data import (
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


def detect_nomen_verb(
    word: str, doc: spacy.tokens.Doc
) -> NomenVerbInfo | None:
    """Detect Nomen-Verb-Verbindungen from context.

    When the user selects a noun or verb, checks if the sentence contains
    a known noun+verb combination.
    """
    word_lower = word.lower()
    target = next((t for t in doc if t.text.lower() == word_lower), None)
    if not target:
        return None

    # Determine noun_token and verb_token based on what was selected
    if target.pos_ == "NOUN":
        return _match_from_noun(target, doc)
    elif target.pos_ == "VERB":
        return _match_from_verb(target, doc)
    elif target.text.lower() == "sich":
        # User selected the reflexive pronoun — try to find the NVV from context
        return _match_from_sich(target, doc)

    return None


def _match_from_noun(
    noun_token, doc: spacy.tokens.Doc
) -> NomenVerbInfo | None:
    """User selected the noun — find a matching verb in the sentence."""
    noun_text = noun_token.text
    noun_lower = noun_text.lower()
    sich_token = _find_sich(doc)

    # First try reflexive prep + noun + verb (longest match, highest priority)
    if sich_token:
        refl_prep_candidates = NOMEN_VERB_PREP_REFLEXIVE_INDEX.get(noun_lower, [])
        if refl_prep_candidates:
            verb_tokens = [t for t in doc if t.pos_ == "VERB"]
            prep_tokens = [t for t in doc if t.pos_ == "ADP"]
            for prep_t in prep_tokens:
                prep_lemma = prep_t.lemma_.lower()
                for verb_t in verb_tokens:
                    verb_lemma = verb_t.lemma_.lower()
                    key = (prep_lemma, noun_text, verb_lemma)
                    if key in NOMEN_VERB_PREP_REFLEXIVE:
                        pattern = NOMEN_VERB_PREP_REFLEXIVE[key]
                        related = [
                            TokenRef(t.text, t.idx)
                            for t in (sich_token, prep_t, verb_t)
                            if t != noun_token
                        ]
                        return NomenVerbInfo(pattern, related)

    # Then try non-reflexive prep + noun + verb
    prep_candidates = NOMEN_VERB_PREP_INDEX.get(noun_lower, [])
    if prep_candidates:
        verb_tokens = [t for t in doc if t.pos_ == "VERB"]
        prep_tokens = [t for t in doc if t.pos_ == "ADP"]

        for prep_t in prep_tokens:
            prep_lemma = prep_t.lemma_.lower()
            for verb_t in verb_tokens:
                verb_lemma = verb_t.lemma_.lower()
                key = (prep_lemma, noun_text, verb_lemma)
                if key in NOMEN_VERB_PREP:
                    pattern = NOMEN_VERB_PREP[key]
                    related = [
                        TokenRef(t.text, t.idx)
                        for t in (prep_t, verb_t)
                        if t != noun_token
                    ]
                    return NomenVerbInfo(pattern, related)

    # Then try simple noun + verb (with or without sich)
    candidates = NOMEN_VERB_INDEX.get(noun_lower, [])
    if not candidates:
        return None

    for verb_t in doc:
        if verb_t.pos_ != "VERB":
            continue
        verb_lemma = verb_t.lemma_.lower()
        key = (noun_text, verb_lemma)
        if key in NOMEN_VERB:
            is_reflexive = key in NOMEN_VERB_REFLEXIVE
            if is_reflexive and not sich_token:
                continue  # skip: sich required but not present
            pattern = NOMEN_VERB[key]
            related_tokens = [verb_t]
            if is_reflexive and sich_token:
                related_tokens.append(sich_token)
            related = [TokenRef(t.text, t.idx) for t in related_tokens]
            return NomenVerbInfo(pattern, related)

    return None


def _match_from_verb(
    verb_token, doc: spacy.tokens.Doc
) -> NomenVerbInfo | None:
    """User selected the verb — find a matching noun in the sentence."""
    verb_lemma = verb_token.lemma_.lower()
    sich_token = _find_sich(doc)

    # Collect all nouns in the sentence
    noun_tokens = [t for t in doc if t.pos_ == "NOUN"]
    if not noun_tokens:
        return None

    prep_tokens = [t for t in doc if t.pos_ == "ADP"]

    # First try reflexive prep + noun + verb (longest match, highest priority)
    if sich_token:
        for noun_t in noun_tokens:
            refl_prep_candidates = NOMEN_VERB_PREP_REFLEXIVE_INDEX.get(noun_t.text.lower(), [])
            for prep_t in prep_tokens:
                prep_lemma = prep_t.lemma_.lower()
                key = (prep_lemma, noun_t.text, verb_lemma)
                if key in NOMEN_VERB_PREP_REFLEXIVE:
                    pattern = NOMEN_VERB_PREP_REFLEXIVE[key]
                    related = [
                        TokenRef(t.text, t.idx)
                        for t in (sich_token, prep_t, noun_t)
                        if t != verb_token
                    ]
                    return NomenVerbInfo(pattern, related)

    # Then try non-reflexive prep + noun + verb
    for noun_t in noun_tokens:
        prep_candidates = NOMEN_VERB_PREP_INDEX.get(noun_t.text.lower(), [])
        for prep_t in prep_tokens:
            prep_lemma = prep_t.lemma_.lower()
            key = (prep_lemma, noun_t.text, verb_lemma)
            if key in NOMEN_VERB_PREP:
                pattern = NOMEN_VERB_PREP[key]
                related = [
                    TokenRef(t.text, t.idx)
                    for t in (prep_t, noun_t)
                    if t != verb_token
                ]
                return NomenVerbInfo(pattern, related)

    # Then try simple noun + verb (with or without sich)
    for noun_t in noun_tokens:
        key = (noun_t.text, verb_lemma)
        if key in NOMEN_VERB:
            is_reflexive = key in NOMEN_VERB_REFLEXIVE
            if is_reflexive and not sich_token:
                continue  # skip: sich required but not present
            pattern = NOMEN_VERB[key]
            related_tokens = [noun_t]
            if is_reflexive and sich_token:
                related_tokens.append(sich_token)
            related = [TokenRef(t.text, t.idx) for t in related_tokens]
            return NomenVerbInfo(pattern, related)

    return None


def _find_sich(doc: spacy.tokens.Doc):
    """Return the 'sich' token if present in the doc, else None."""
    for t in doc:
        if t.text.lower() == "sich":
            return t
    return None


def _match_from_sich(
    sich_token, doc: spacy.tokens.Doc
) -> NomenVerbInfo | None:
    """User selected 'sich' — find a matching reflexive NVV in context."""
    verb_tokens = [t for t in doc if t.pos_ == "VERB"]
    noun_tokens = [t for t in doc if t.pos_ == "NOUN"]
    prep_tokens = [t for t in doc if t.pos_ == "ADP"]

    # Try reflexive prep + noun + verb first (longest match)
    for noun_t in noun_tokens:
        refl_prep_candidates = NOMEN_VERB_PREP_REFLEXIVE_INDEX.get(noun_t.text.lower(), [])
        for prep_t in prep_tokens:
            prep_lemma = prep_t.lemma_.lower()
            for verb_t in verb_tokens:
                verb_lemma = verb_t.lemma_.lower()
                key = (prep_lemma, noun_t.text, verb_lemma)
                if key in NOMEN_VERB_PREP_REFLEXIVE:
                    pattern = NOMEN_VERB_PREP_REFLEXIVE[key]
                    related = [
                        TokenRef(t.text, t.idx)
                        for t in (prep_t, noun_t, verb_t)
                        if t != sich_token
                    ]
                    return NomenVerbInfo(pattern, related)

    # Then try simple reflexive noun + verb
    for noun_t in noun_tokens:
        for verb_t in verb_tokens:
            key = (noun_t.text, verb_t.lemma_.lower())
            if key in NOMEN_VERB_REFLEXIVE:
                pattern = NOMEN_VERB[key]
                related = [
                    TokenRef(t.text, t.idx)
                    for t in (noun_t, verb_t)
                    if t != sich_token
                ]
                return NomenVerbInfo(pattern, related)

    return None

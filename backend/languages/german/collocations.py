"""German verb+preposition collocation detection."""

from dataclasses import dataclass

import spacy
from models import TokenRef
from languages.german.collocation_data import VERB_PREPOSITION_COLLOCATIONS
from languages.german.verbs import REFLEXIVE_PRONOUNS


@dataclass
class CollocationInfo:
    """Internal: verb+preposition collocation info."""
    verb: str
    pattern: str
    related: list[TokenRef]


def _find_reflexive(doc: spacy.tokens.Doc):
    """Return the reflexive pronoun token (sich/mich/dich/uns/euch) if present, else None."""
    for t in doc:
        if t.text.lower() in REFLEXIVE_PRONOUNS:
            return t
    return None


def _is_reflexive_pronoun(word: str) -> bool:
    """Check if a word is a German reflexive pronoun."""
    return word.lower() in REFLEXIVE_PRONOUNS


def _find_collocation(target, verb_token, prep_token, doc):
    """Check if verb+prep is a known collocation and return CollocationInfo."""
    prefix = next((t for t in doc if t.head == verb_token and t.tag_ == "PTKVZ"), None)
    full_lemma = (prefix.text.lower() + verb_token.lemma_) if prefix else verb_token.lemma_
    prep = prep_token.text.lower()

    for lemma in (full_lemma, verb_token.lemma_):
        if (lemma, prep) in VERB_PREPOSITION_COLLOCATIONS:
            pattern = VERB_PREPOSITION_COLLOCATIONS[(lemma, prep)]

            # Collect related tokens (all parts except the selected word)
            parts = [verb_token, prep_token, prefix]

            # If the pattern starts with "sich", include the reflexive pronoun in related tokens
            if pattern.startswith("sich "):
                refl_token = _find_reflexive(doc)
                if refl_token:
                    parts.append(refl_token)

            related = [
                TokenRef(t.text, t.idx)
                for t in parts
                if t and t != target
            ]
            return CollocationInfo(lemma, pattern, related)
    return None


def detect_verb_preposition_collocation(
    target, doc: spacy.tokens.Doc
) -> CollocationInfo | None:
    """Detect verb+preposition collocations from context.

    Args:
        target: The resolved spaCy token the user selected
        doc: spaCy Doc of the context
    """
    # Determine verb_token and prep_token based on what was selected
    verb_token, prep_token = None, None
    if target.tag_ == "PTKVZ" and target.head.pos_ == "VERB":
        verb_token = target.head
        prep_token = next((t for t in doc if t.pos_ == "ADP" and t.tag_ != "PTKVZ"), None)
    elif target.pos_ == "VERB":
        verb_token = target
        prep_token = next((t for t in doc if t.pos_ == "ADP" and t.tag_ != "PTKVZ"), None)
    elif target.pos_ == "ADP":
        prep_token = target
        verb_token = next((t for t in doc if t.pos_ == "VERB"), None)
    elif _is_reflexive_pronoun(target.text.lower()):
        # User selected a reflexive pronoun (sich/mich/dich/uns/euch) — find verb and preposition
        verb_token = next((t for t in doc if t.pos_ == "VERB"), None)
        prep_token = next((t for t in doc if t.pos_ == "ADP" and t.tag_ != "PTKVZ"), None)

    if verb_token and prep_token:
        return _find_collocation(target, verb_token, prep_token, doc)
    return None

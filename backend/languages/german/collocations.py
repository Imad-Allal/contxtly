"""German verb+preposition collocation detection."""

from dataclasses import dataclass

import spacy
from models import TokenRef
from languages.german.collocation_data import VERB_PREPOSITION_COLLOCATIONS


@dataclass
class CollocationInfo:
    """Internal: verb+preposition collocation info (e.g., "von etwas ausgehen")."""
    verb: str           # e.g., "ausgehen"
    pattern: str        # e.g., "von etwas ausgehen"
    related: list[TokenRef]


def detect_verb_preposition_collocation(
    word: str, doc: spacy.tokens.Doc
) -> CollocationInfo | None:
    """Detect verb+preposition collocations from context."""
    word_lower = word.lower()
    target = next((t for t in doc if t.text.lower() == word_lower), None)
    if not target:
        return None

    def find_collocation(verb_token, prep_token):
        """Check if verb+prep is a known collocation and return CollocationInfo."""
        prefix = next((t for t in doc if t.head == verb_token and t.tag_ == "PTKVZ"), None)
        full_lemma = (prefix.text.lower() + verb_token.lemma_) if prefix else verb_token.lemma_
        prep = prep_token.text.lower()

        for lemma in (full_lemma, verb_token.lemma_):
            if (lemma, prep) in VERB_PREPOSITION_COLLOCATIONS:
                pattern = VERB_PREPOSITION_COLLOCATIONS[(lemma, prep)]
                related = [
                    TokenRef(t.text, t.idx)
                    for t in (verb_token, prep_token, prefix)
                    if t and t != target
                ]
                return CollocationInfo(lemma, pattern, related)
        return None

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

    if verb_token and prep_token:
        return find_collocation(verb_token, prep_token)
    return None

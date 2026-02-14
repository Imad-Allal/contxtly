"""German adverbial locution detection."""

from dataclasses import dataclass

import spacy
from models import TokenRef
from languages.german.adverbial_data import ADVERBIAL_INDEX


@dataclass
class AdverbialLocutionInfo:
    """Detected adverbial locution (e.g., "auf jeden Fall")."""
    locution: str           # canonical form: "auf jeden Fall"
    related: list[TokenRef] # all parts except the selected word


def detect_adverbial_locution(
    word: str, doc: spacy.tokens.Doc
) -> AdverbialLocutionInfo | None:
    """Detect adverbial locutions from context.

    Looks up the selected word in the reverse index, then checks if any
    candidate locution matches a contiguous sequence of tokens in the doc.
    Returns the longest match.
    """
    word_lower = word.lower()
    candidates = ADVERBIAL_INDEX.get(word_lower)
    if not candidates:
        return None

    # Build token list from doc (text + index)
    doc_tokens = [(t.text, t.idx) for t in doc]
    doc_lower = [t.text.lower() for t in doc]

    best: AdverbialLocutionInfo | None = None

    for candidate in candidates:
        match = _find_contiguous_match(candidate, doc_tokens, doc_lower, word_lower)
        if match and (best is None or len(candidate) > len(best.locution.split())):
            best = match

    return best


def _find_contiguous_match(
    candidate: tuple[str, ...],
    doc_tokens: list[tuple[str, int]],
    doc_lower: list[str],
    selected_word: str,
) -> AdverbialLocutionInfo | None:
    """Try to find a contiguous token sequence matching the candidate tuple.

    Returns AdverbialLocutionInfo if found and the selected word is part of it.
    """
    candidate_lower = [w.lower() for w in candidate]
    cand_len = len(candidate_lower)

    for start in range(len(doc_lower) - cand_len + 1):
        if doc_lower[start:start + cand_len] == candidate_lower:
            # Found a match — check if selected word is in it
            matched_tokens = doc_tokens[start:start + cand_len]
            selected_in_match = any(
                text.lower() == selected_word for text, _ in matched_tokens
            )
            if not selected_in_match:
                continue

            # Build related list (all parts except the selected word — first occurrence only)
            locution = " ".join(text for text, _ in matched_tokens)
            related = []
            selected_found = False
            for text, offset in matched_tokens:
                if not selected_found and text.lower() == selected_word:
                    selected_found = True
                    continue
                related.append(TokenRef(text, offset))

            return AdverbialLocutionInfo(locution=locution, related=related)

    return None

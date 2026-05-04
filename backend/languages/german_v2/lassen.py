"""V2 lassen-construction detection.

Wraps v1's detect_lassen_construction with a fix for a spaCy lemma
quirk: spaCy de_core_news_lg returns lemma_='lässt' for the surface
form 'lässt' (and similarly for other forms), instead of the correct
'lassen'. The v1 detector relies on `t.lemma_ == "lassen"` to find the
governing verb, which silently misses these cases.

This wrapper corrects the lemma at lookup time without modifying v1.
"""

import spacy

from languages.german.verbs import (
    detect_lassen_construction as _v1_detect_lassen,
    LassenInfo,
)


# All surface forms of "lassen" we want to recognise as the lemma "lassen"
_LASSEN_SURFACES = frozenset({
    "lassen", "lässt", "lass", "lasst",
    "ließ", "ließen", "ließt", "ließest",
    "gelassen",
})


class _LemmaPatch:
    """Wrap a spaCy Doc, monkey-patching lemma_ access for lassen-forms.

    spaCy Tokens are immutable from Python, so we can't set lemma_
    directly. Instead, we use a dependency-injection trick: the v1
    detector reads `t.lemma_`. We pre-populate a mapping from token
    index to a corrected lemma, but we'd need to actually wrap the
    docs — which is fiddly. Easier path: just call v1 first (catches
    the case where target IS a lassen surface), and if that fails,
    fall back to a manual scan that uses surface-text matching.
    """


def _find_lassen_token(doc, exclude_idx: int | None = None):
    """Find a token in `doc` whose surface or lemma matches lassen."""
    for t in doc:
        if exclude_idx is not None and t.i == exclude_idx:
            continue
        if t.lemma_ == "lassen":
            return t
        if t.text.lower() in _LASSEN_SURFACES and t.pos_ in ("VERB", "AUX"):
            return t
    return None


def _find_inf_verb(doc, exclude_idx: int | None = None):
    """Find an infinitive verb in the doc that isn't excluded."""
    for t in doc:
        if exclude_idx is not None and t.i == exclude_idx:
            continue
        if t.pos_ == "VERB" and "Inf" in (t.morph.get("VerbForm") or []):
            return t
    return None


def _find_sich(doc):
    for t in doc:
        if t.text.lower() == "sich":
            return t
    return None


def detect_lassen_construction(target, doc: spacy.tokens.Doc) -> LassenInfo | None:
    """V2 lassen detector — tolerant of spaCy's lemma quirk.

    Strategy:
      1. Try v1 first (handles the canonical case where target is a
         lassen surface form OR a verb whose head is correctly
         lemmatised to 'lassen').
      2. If v1 misses AND target is a verb, do a manual scan: find
         any token in the sentence matching a lassen surface form;
         pair it with target.
    """
    v1_result = _v1_detect_lassen(target, doc)
    if v1_result is not None:
        return v1_result

    # Fallback: target is a verb, and a lassen surface form exists in the
    # sentence that v1 missed because of the lemma issue.
    if target.pos_ != "VERB":
        return None

    sent = target.sent if target.sent is not None else doc
    sent_tokens = list(sent)

    lassen_token = None
    for t in sent_tokens:
        if t.i == target.i:
            continue
        if t.text.lower() in _LASSEN_SURFACES and t.pos_ in ("VERB", "AUX"):
            lassen_token = t
            break

    if lassen_token is None:
        return None

    # Build a LassenInfo by hand
    lassen_morph = {}
    for item in lassen_token.morph:
        if "=" in item:
            k, v = item.split("=", 1)
            lassen_morph[k] = v

    # spaCy lemma for the verb might also be wrong (e.g. would-be irregular);
    # use simplemma defensively.
    try:
        import simplemma
        verb_infinitive = simplemma.lemmatize(target.text, lang="de") or target.lemma_ or target.text
    except Exception:
        verb_infinitive = target.lemma_ or target.text

    sich_token = _find_sich(sent_tokens)

    return LassenInfo(
        verb_infinitive=verb_infinitive,
        lassen_token_text=lassen_token.text,
        lassen_token_idx=lassen_token.idx,
        lassen_morph=lassen_morph,
        verb_token_text=target.text,
        verb_token_idx=target.idx,
        has_sich=sich_token is not None,
        sich_token_text=sich_token.text if sich_token else None,
        sich_token_idx=sich_token.idx if sich_token else None,
    )

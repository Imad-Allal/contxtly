"""V2 n-Deklination detection.

Weak masculine nouns (Mensch, Student, Junge, Herr, Bär, …) add -n or
-en in every case except nominative singular. Common learner trap —
they say "der Studenten" or "den Student" instead of the correct "den
Studenten".

When the user selects a noun whose lemma is in the n-Deklination
class AND the surface form differs from the lemma (i.e. it's
inflected), we flag it so the breakdown can explain the rule.

Pure morphology + dict lookup — data lives in `german_n_decl` /
`dict_store.N_DECL_LEMMAS`.
"""

from dataclasses import dataclass

import spacy

from languages.german.dict_store import N_DECL_LEMMAS


@dataclass
class NDeklinationInfo:
    """Detected n-Deklination usage."""
    surface: str               # 'Studenten', 'Menschen', …
    surface_idx: int
    lemma: str                 # 'Student', 'Mensch', …
    is_lemma_form: bool        # True iff surface == lemma (nom sg)


def detect_n_declination(target, doc: spacy.tokens.Doc) -> NDeklinationInfo | None:
    """Detect a weak masculine noun (n-Deklination).

    Fires when:
      - target is a noun
      - target.lemma_ (or target.text) is in the curated n-Dekl set

    Returns NDeklinationInfo. The detector emits a candidate even when
    the form is the bare lemma (nominative singular) so the UI can
    show the rule to learners on every encounter.
    """
    if target.pos_ != "NOUN":
        return None

    if not N_DECL_LEMMAS:
        return None

    # Try lemma first, then surface — covers both "Studenten" → lemma
    # "Student" → matches, AND "Student" itself.
    lemma_candidates = [
        (target.lemma_ or "").strip(),
        target.text.strip(),
    ]
    matched_lemma: str | None = None
    for cand in lemma_candidates:
        if cand and cand in N_DECL_LEMMAS:
            matched_lemma = cand
            break

    if matched_lemma is None:
        return None

    return NDeklinationInfo(
        surface=target.text,
        surface_idx=target.idx,
        lemma=matched_lemma,
        is_lemma_form=target.text == matched_lemma,
    )

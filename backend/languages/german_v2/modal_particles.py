"""V2 modal particle (Modalpartikel / Abtönungspartikel) detection.

German modal particles — *doch, ja, mal, halt, eben, schon, denn,
bloß, wohl, etwa, ruhig, eigentlich, aber, nur, vielleicht, überhaupt,
gar, eh, sowieso, nun, immerhin, gell, fei* — carry pragmatic meaning
rather than lexical content. They're the soul of spoken German and
the v1 backend has zero handling.

Data lives in the german_modal_particle table (loaded into
dict_store.MODAL_PARTICLES at startup). This module is logic only:

  1. Identify the candidate token by lemma/text in MODAL_PARTICLES
  2. Reject obvious non-particle uses (denn-as-conjunction,
     ja-as-affirmation, mal-as-multiplier) via cheap position heuristics
  3. Infer sentence type from punctuation and word order
  4. Look up the (particle, sentence_type) reading in MODAL_PARTICLES
  5. If a reading exists, emit a ParticleInfo
"""

from dataclasses import dataclass

import spacy

from languages.german.dict_store import MODAL_PARTICLES


@dataclass
class ParticleInfo:
    """Detected modal particle with its inferred reading."""
    particle_text: str
    particle_idx: int
    sentence_type: str         # 'declarative' | 'interrogative' | 'imperative'
    reading: str
    canonical: str             # e.g. "doch (Modalpartikel — softening)"


# spaCy PoS tags a modal particle could carry. spaCy's de_core_news_lg is
# inconsistent (sometimes ADV, sometimes PART, occasionally INTJ); we accept
# the broad set, then disambiguate via position.
_PARTICLE_OK_POS = {"PART", "ADV", "INTJ", ""}


def _sentence_type(target_token, doc: spacy.tokens.Doc) -> str:
    """Infer the sentence type of the sentence containing target_token.

    Heuristics:
      - ends with '?'                              → interrogative
      - first content token is a finite verb/aux   → imperative
        (German V1 questions also start with a verb but those end with '?')
      - otherwise                                  → declarative
    """
    sent = target_token.sent if target_token.sent is not None else doc
    sent_tokens = list(sent)
    if not sent_tokens:
        return "declarative"

    last = sent_tokens[-1]
    if last.text == "?":
        return "interrogative"

    first_content = next(
        (t for t in sent_tokens if not t.is_punct and not t.is_space),
        None,
    )
    if first_content is not None:
        # spaCy de_core_news_lg sometimes mis-tags imperative verbs as ADV
        # but keeps the correct STTS tag (VVIMP / VAIMP). Accept either
        # signal.
        is_verb_pos = first_content.pos_ in ("VERB", "AUX")
        is_imperative_tag = first_content.tag_ in ("VVIMP", "VAIMP")
        if is_imperative_tag:
            return "imperative"
        if is_verb_pos:
            verb_form = first_content.morph.get("VerbForm")
            mood = first_content.morph.get("Mood")
            if mood == "Imp":
                return "imperative"
            if not verb_form or verb_form == "Fin":
                return "imperative"

        # Fallback: spaCy sometimes loses short imperatives entirely
        # ("Geh nach Hause" → tagged as ADV with empty morph). If the
        # sentence has NO verb-tagged token anywhere, the first content
        # token is almost certainly a mis-tagged imperative.
        has_any_verb = any(
            t.pos_ in ("VERB", "AUX") or t.tag_.startswith("V")
            for t in sent_tokens
        )
        if not has_any_verb:
            return "imperative"

    return "declarative"


def _looks_like_particle(target, doc: spacy.tokens.Doc) -> bool:
    """Reject obvious non-particle uses for ambiguous lemmas.

    - 'denn' / 'aber' at the start of a clause OR after a comma → conjunction
    - 'mal' immediately preceded by a number → multiplier
    - 'ja' as a one-content-token sentence → affirmation
    - 'nur' / 'vielleicht' / 'nun' have lexical readings — accept here and
      let the sentence-type lookup filter (their particle readings are
      tied to specific sentence types via the MODAL_PARTICLES table)
    """
    text = target.text.lower()
    sent = target.sent if target.sent is not None else doc
    sent_tokens = [t for t in sent if not t.is_space]
    if not sent_tokens:
        return False

    first = next((t for t in sent_tokens if not t.is_punct), None)

    if text in {"denn", "aber"}:
        if first is not None and first.i == target.i:
            return False
        prev = doc[target.i - 1] if target.i > 0 else None
        if prev is not None and prev.text == ",":
            return False

    if text == "mal":
        prev = doc[target.i - 1] if target.i > 0 else None
        if prev is not None and (prev.like_num or prev.pos_ == "NUM"):
            return False

    if text == "ja":
        content = [t for t in sent_tokens if not t.is_punct]
        if len(content) <= 1:
            return False

    return True


def detect_modal_particle(target, doc: spacy.tokens.Doc) -> ParticleInfo | None:
    """Detect a German modal particle at the target token.

    Returns ParticleInfo when:
      - target lower-cased text is in the MODAL_PARTICLES table
      - PoS is consistent with a particle reading
      - position isn't a clear non-particle use
      - a reading exists for the inferred sentence type

    Otherwise returns None.
    """
    text = target.text.lower()

    # Quick membership check against the loaded table; cheap exit when this
    # token isn't a known particle.
    if not any(p == text for (p, _) in MODAL_PARTICLES):
        return None

    if target.pos_ not in _PARTICLE_OK_POS:
        return None

    if not _looks_like_particle(target, doc):
        return None

    sent_type = _sentence_type(target, doc)
    reading = MODAL_PARTICLES.get((text, sent_type))
    if not reading:
        return None

    return ParticleInfo(
        particle_text=target.text,
        particle_idx=target.idx,
        sentence_type=sent_type,
        reading=reading,
        canonical=f"{target.text} (Modalpartikel — {reading})",
    )

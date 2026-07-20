"""V2 Imperativ detection.

German imperative forms can be morphologically obvious ("Komm!", VVIMP
tag) or completely lost by spaCy (tagged ADV with empty morph). We
catch both via a tiered check.

A token is treated as an imperative when:
  - target tag is VVIMP or VAIMP (German imperative tag), OR
  - target morph has Mood=Imp, OR
  - target is the first content token of a sentence with NO other
    verb-tagged token AND the sentence ends with '!' or has no
    explicit subject pronoun

The third tier is the fallback for short imperatives like "Geh!" /
"Sag!" that spaCy mis-tags as ADV.
"""

from dataclasses import dataclass

import simplemma
import spacy


@dataclass
class ImperativeInfo:
    """Detected imperative verb."""
    surface: str
    surface_idx: int
    lemma: str
    person_form: str          # 'du' / 'ihr' / 'Sie' — singular informal / plural / formal


def _morph_has(token, key: str, value: str) -> bool:
    """spaCy's MorphAnalysis.get returns a list, not a string — wrap it."""
    return value in (token.morph.get(key) or [])


def _is_imperative_token(token, doc: spacy.tokens.Doc) -> bool:
    """Return True if the token is (or is mis-tagged as) an imperative verb."""
    if token.tag_ in ("VVIMP", "VAIMP"):
        return True
    if _morph_has(token, "Mood", "Imp"):
        return True

    # Fallback: short imperatives mis-tagged as ADV with empty morph.
    sent = token.sent if token.sent is not None else doc
    sent_tokens = [t for t in sent if not t.is_space]
    if not sent_tokens:
        return False
    first_content = next((t for t in sent_tokens if not t.is_punct), None)
    # spaCy Tokens aren't singletons — compare by index, not identity
    if first_content is None or first_content.i != token.i:
        return False
    if token.pos_ in ("VERB", "AUX"):
        return False  # already verb-tagged but no Mood — not enough signal
    has_other_verb = any(
        t.i != token.i and (t.pos_ in ("VERB", "AUX") or t.tag_.startswith("V"))
        for t in sent_tokens
    )
    if has_other_verb:
        return False
    # No verb anywhere AND token starts the sentence — likely a verb spaCy lost
    lemma = simplemma.lemmatize(token.text.lower(), lang="de")
    if not lemma or lemma == token.text.lower():
        return False  # simplemma didn't recognise it as a verb
    return True


def _person_form(token) -> str:
    """Infer the imperative addressee form (du / ihr / Sie)."""
    if _morph_has(token, "Person", "2") and _morph_has(token, "Number", "Sing"):
        return "du"
    if _morph_has(token, "Person", "2") and _morph_has(token, "Number", "Plur"):
        return "ihr"
    # Sie-form imperative: verb + Sie ("Kommen Sie!")
    sent = token.sent if token.sent is not None else None
    if sent is not None:
        for t in sent:
            if t.text == "Sie" and t.i > token.i:
                return "Sie"
    # Default — singular informal
    return "du"


def detect_imperative(target, doc: spacy.tokens.Doc) -> ImperativeInfo | None:
    if not _is_imperative_token(target, doc):
        return None

    lemma = simplemma.lemmatize(target.text.lower(), lang="de") or target.lemma_ or target.text
    return ImperativeInfo(
        surface=target.text,
        surface_idx=target.idx,
        lemma=lemma.lower(),
        person_form=_person_form(target),
    )

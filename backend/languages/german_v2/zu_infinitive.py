"""V2 zu-Infinitiv detection.

Three syntactic shapes:
  1. "zu" + infinitive   ("Ich versuche, zu gehen")
  2. Fused VVIZU         ("abzuwarten" — separable verb with embedded zu)
  3. Introduced clauses  ("um zu ...", "ohne zu ...", "statt/anstatt zu ...")

Returns ZuInfInfo when:
  - target token is the verb (the infinitive itself), or
  - target token is the "zu" particle, or
  - target token is the introducer (um/ohne/statt/anstatt) and a
    zu-infinitive follows in the same sentence

Pure morphology — no DB data.
"""

from dataclasses import dataclass

import simplemma
import spacy
from models import TokenRef


# Introducers that head a zu-infinitive purpose/manner clause
_INTRODUCERS = {"um", "ohne", "statt", "anstatt"}


@dataclass
class ZuInfInfo:
    """Detected zu-Infinitiv construction."""
    infinitive: str            # the infinitive verb's lemma
    surface: str               # full surface form (e.g. "zu gehen" or "abzuwarten")
    introducer: str | None     # 'um' / 'ohne' / 'statt' / 'anstatt' / None
    related: list[TokenRef]    # other tokens covered (zu, introducer, etc.)


def _is_fused_zu_infinitive(token) -> bool:
    """VVIZU is the German tag for fused zu+infinitive (e.g. 'abzuwarten')."""
    return token.tag_ == "VVIZU"


def _find_introducer(verb_token, doc: spacy.tokens.Doc):
    """Return the (introducer_token, zu_token | None) pair for a zu-inf clause, or (None, None)."""
    sent = verb_token.sent if verb_token.sent is not None else doc
    sent_tokens = list(sent)
    # Walk left from the verb looking for "zu" then an introducer
    zu_token = None
    for t in reversed([x for x in sent_tokens if x.i < verb_token.i]):
        if zu_token is None and t.text.lower() == "zu":
            zu_token = t
            continue
        if zu_token is not None and t.text.lower() in _INTRODUCERS:
            return (t, zu_token)
        # If we see a non-zu non-introducer non-punct between, give up
        if zu_token is not None and not t.is_punct:
            break
    return (None, zu_token)


def detect_zu_infinitive(target, doc: spacy.tokens.Doc) -> ZuInfInfo | None:
    """Detect a zu-Infinitiv construction at the target token.

    Selection points the user might click:
      - the infinitive verb (gehen / abwarten)
      - the "zu" particle
      - the introducer (um/ohne/statt/anstatt)
    """
    sent = target.sent if target.sent is not None else doc
    sent_tokens = list(sent)

    # Case A: target is a fused VVIZU token (abzuwarten, mitzunehmen, …)
    if _is_fused_zu_infinitive(target):
        infinitive = simplemma.lemmatize(target.text.lower(), lang="de") or target.lemma_ or target.text
        introducer, _ = _find_introducer(target, doc)
        related: list[TokenRef] = []
        if introducer is not None:
            related.append(TokenRef(introducer.text, introducer.idx))
        return ZuInfInfo(
            infinitive=infinitive.lower(),
            surface=target.text,
            introducer=introducer.text.lower() if introducer is not None else None,
            related=related,
        )

    # Case B: target is the infinitive (Inf VerbForm) preceded by a "zu" particle
    if target.pos_ == "VERB" and "Inf" in (target.morph.get("VerbForm") or []):
        # Look for "zu" immediately or within 2 tokens before
        zu_token = None
        for t in reversed([x for x in sent_tokens if x.i < target.i]):
            if t.text.lower() == "zu":
                zu_token = t
                break
            if not t.is_punct:
                break  # something else in between — not a zu-Inf
        if zu_token is None:
            return None
        introducer, _ = _find_introducer(target, doc)
        infinitive = simplemma.lemmatize(target.text.lower(), lang="de") or target.lemma_ or target.text
        related = [TokenRef(zu_token.text, zu_token.idx)]
        if introducer is not None:
            related.append(TokenRef(introducer.text, introducer.idx))
        return ZuInfInfo(
            infinitive=infinitive.lower(),
            surface=f"{zu_token.text} {target.text}",
            introducer=introducer.text.lower() if introducer is not None else None,
            related=related,
        )

    # Case C: target is the "zu" particle — find the following infinitive
    if target.text.lower() == "zu" and target.tag_ == "PTKZU":
        verb = next(
            (t for t in sent_tokens
             if t.i > target.i
             and t.pos_ == "VERB"
             and t.morph.get("VerbForm") == "Inf"),
            None,
        )
        if verb is None:
            return None
        introducer, _ = _find_introducer(verb, doc)
        infinitive = simplemma.lemmatize(verb.text.lower(), lang="de") or verb.lemma_ or verb.text
        related = [TokenRef(verb.text, verb.idx)]
        if introducer is not None:
            related.append(TokenRef(introducer.text, introducer.idx))
        return ZuInfInfo(
            infinitive=infinitive.lower(),
            surface=f"{target.text} {verb.text}",
            introducer=introducer.text.lower() if introducer is not None else None,
            related=related,
        )

    # Case D: target is an introducer (um/ohne/statt/anstatt) — find zu+inf after it
    if target.text.lower() in _INTRODUCERS:
        # Look for zu + Inf in the same sentence after the introducer
        for t in sent_tokens:
            if t.i <= target.i:
                continue
            if t.tag_ == "VVIZU":
                infinitive = simplemma.lemmatize(t.text.lower(), lang="de") or t.lemma_ or t.text
                return ZuInfInfo(
                    infinitive=infinitive.lower(),
                    surface=f"{target.text} {t.text}",
                    introducer=target.text.lower(),
                    related=[TokenRef(t.text, t.idx)],
                )
            if t.text.lower() == "zu" and t.tag_ == "PTKZU":
                # Look for Inf immediately after
                verb = next(
                    (x for x in sent_tokens
                     if x.i > t.i and x.pos_ == "VERB"
                     and "Inf" in (x.morph.get("VerbForm") or [])),
                    None,
                )
                if verb is not None:
                    infinitive = simplemma.lemmatize(verb.text.lower(), lang="de") or verb.lemma_ or verb.text
                    return ZuInfInfo(
                        infinitive=infinitive.lower(),
                        surface=f"{target.text} {t.text} {verb.text}",
                        introducer=target.text.lower(),
                        related=[TokenRef(t.text, t.idx), TokenRef(verb.text, verb.idx)],
                    )

    return None

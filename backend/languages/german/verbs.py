"""German verb detection: separable verbs and compound tenses."""

from dataclasses import dataclass

import simplemma
import spacy
from models import TokenRef

# All forms of the German reflexive pronoun
REFLEXIVE_PRONOUNS = frozenset({"mich", "dich", "sich", "uns", "euch"})

# Known separable verb prefixes - used as fallback when spaCy misses PTKVZ tagging
SEPARABLE_PREFIXES = frozenset({
    "ab", "an", "auf", "aus", "bei", "ein", "fest", "her", "hin", "los",
    "mit", "nach", "vor", "weg", "zu", "zurück", "zusammen", "weiter",
    "da", "dar", "empor", "fort", "heim", "nieder", "um", "vorbei",
})


def detect_separable_verb(target_token, doc: spacy.tokens.Doc) -> tuple[str, TokenRef] | None:
    """
    Detect if a verb is part of a separable verb construction.

    Example: "Ich ziehe mich an" → "ziehe" is part of "anziehen"

    Args:
        target_token: The resolved spaCy token the user selected
        doc: spaCy Doc of the context

    Returns:
        Tuple of (infinitive, prefix_ref) or None if not separable
    """
    if target_token.pos_ not in ("VERB", "AUX"):
        return None

    for token in doc:
        if token.head != target_token:
            continue
        # Skip "zu" infinitive particle (e.g., "zu gehen") — not a separable prefix
        # spaCy tags separable "zu" as PTKVZ, infinitive "zu" as PTKZU
        if token.tag_ == "PTKZU":
            continue
        is_particle = token.tag_ == "PTKVZ" or token.dep_ == "svp"
        is_known_prefix = (token.text.lower() in SEPARABLE_PREFIXES
                           and token.pos_ not in ("DET", "PRON", "NOUN")
                           and token.dep_ not in ("nk", "mo", "sb", "og", "da", "oa"))
        if is_particle or is_known_prefix:
            # Lemmatize the verb using simplemma (more reliable than spaCy for irregular verbs)
            verb_lemma = simplemma.lemmatize(target_token.text, lang="de")
            infinitive = token.text.lower() + verb_lemma
            return (infinitive, TokenRef(token.text, token.idx))

    return None


def detect_separable_verb_from_prefix(target_token, doc: spacy.tokens.Doc) -> tuple[str, str, dict, int] | None:
    """
    Detect full separable verb when user selects the prefix/particle.

    Example: "Er legte das Buch nieder" → "nieder" → "niederlegen"

    Args:
        target_token: The resolved spaCy token the user selected
        doc: spaCy Doc of the context

    Returns:
        Tuple of (infinitive, verb_text, verb_morph, verb_offset) or None if not a separable verb particle
    """
    # Check if this token is a separable verb particle (PTKVZ tag, svp dependency, or known prefix)
    is_particle = target_token.tag_ == "PTKVZ" or target_token.dep_ == "svp"
    is_known_prefix = (target_token.text.lower() in SEPARABLE_PREFIXES
                       and target_token.pos_ not in ("DET", "PRON", "NOUN")
                       and target_token.dep_ not in ("nk", "mo", "sb", "og", "da", "oa"))
    if not is_particle and not is_known_prefix:
        return None

    # The head of the particle is the verb stem
    # Trust PTKVZ tagging even if verb is misclassified (e.g. imperatives tagged as NOUN),
    # but only when spaCy explicitly tagged the particle (PTKVZ/svp) — not the heuristic path.
    verb_token = target_token.head
    if verb_token.pos_ == "NOUN" and not is_particle:
        return None
    if verb_token.pos_ not in ("VERB", "NOUN", "AUX"):
        return None

    # Parse verb morphology
    verb_morph = {}
    for item in verb_token.morph:
        if "=" in item:
            key, val = item.split("=", 1)
            verb_morph[key] = val

    # Lemmatize the verb using simplemma (more reliable than spaCy for irregular verbs)
    verb_lemma = simplemma.lemmatize(verb_token.text, lang="de")
    infinitive = target_token.text.lower() + verb_lemma
    return (infinitive, verb_token.text, verb_morph, verb_token.idx)


# German compound tense patterns
# Note: ("werden", "Pres", "Part") is handled separately in detect_compound_tense()
# because it is ambiguous between Vorgangspassiv Präsens and Futur II.
GERMAN_COMPOUND_TENSES = {
    ("haben", "Pres", "Part"): "Perfekt (present perfect)",
    ("sein", "Pres", "Part"): "Perfekt (present perfect)",
    ("haben", "Past", "Part"): "Plusquamperfekt (past perfect)",
    ("sein", "Past", "Part"): "Plusquamperfekt (past perfect)",
    ("werden", "Pres", "Inf"): "Futur I (future)",
    ("werden", "Past", "Part"): "Vorgangspassiv Präteritum (past passive)",
    ("werden", "Sub", "Inf"): "Konjunktiv II (subjunctive)",
}

GERMAN_AUXILIARIES = {"haben", "sein", "werden"}


def _are_syntactically_related(aux, main_verb) -> bool:
    """Check if auxiliary and main verb are in the same verb group (dependency-linked)."""
    # Direct relationship: one is the head of the other
    if main_verb.head == aux or aux.head == main_verb:
        return True
    # Same head (siblings in the dependency tree)
    if main_verb.head == aux.head:
        return True
    # Auxiliary is ancestor of main verb (within 2 hops)
    head = main_verb.head
    for _ in range(2):
        if head == aux:
            return True
        head = head.head
    return False


def detect_compound_tense(main_verb, doc: spacy.tokens.Doc) -> str | None:
    """Detect German compound tenses by analyzing auxiliary + main verb patterns.

    Args:
        main_verb: The resolved spaCy token the user selected
        doc: spaCy Doc of the context
    """
    # Find the closest syntactically-related auxiliary
    best_aux = None
    for token in doc:
        if token.lemma_ in GERMAN_AUXILIARIES and _are_syntactically_related(token, main_verb):
            best_aux = token
            break

    if not best_aux:
        return None

    aux_morph = dict(best_aux.morph.to_dict())
    main_morph = dict(main_verb.morph.to_dict())

    aux_lemma = best_aux.lemma_
    aux_tense = aux_morph.get("Tense") or aux_morph.get("Mood", "")
    main_form = main_morph.get("VerbForm", "")

    key = (aux_lemma, aux_tense, main_form)

    # Disambiguate: werden (Pres) + Partizip II is either present passive or Futur II.
    # Futur II requires a second auxiliary (haben/sein) also linked to the main verb;
    # present passive has only werden.
    if key == ("werden", "Pres", "Part"):
        has_second_aux = any(
            token.lemma_ in {"haben", "sein"}
            and _are_syntactically_related(token, main_verb)
            for token in doc
        )
        return "Futur II (future perfect)" if has_second_aux else "Vorgangspassiv Präsens (present passive)"

    return GERMAN_COMPOUND_TENSES.get(key)


# German modal verbs
GERMAN_MODALS = frozenset({"können", "müssen", "sollen", "dürfen", "wollen", "mögen"})


@dataclass
class ModalVerbInfo:
    """Detected modal verb + infinitive construction."""
    modal_text: str        # conjugated modal form (e.g., "will")
    modal_idx: int         # character offset of modal
    modal_lemma: str       # modal infinitive (e.g., "wollen")
    modal_morph: dict[str, str]  # morphology of the modal
    verb_text: str         # the main verb text (e.g., "begrenzen")
    verb_idx: int          # character offset of the main verb
    verb_lemma: str        # infinitive of the main verb
    selected: str          # "modal" or "verb" — which token the user selected
    cluster: list[tuple[str, int]] = None  # additional verbs in cluster [(text, idx), ...]


def detect_modal_verb(target, doc: spacy.tokens.Doc) -> ModalVerbInfo | None:
    """Detect modal verb + infinitive constructions.

    Works when user selects either the modal verb (e.g., "will") or
    the infinitive (e.g., "begrenzen").

    Args:
        target: The resolved spaCy token the user selected
        doc: spaCy Doc of the context

    Returns:
        ModalVerbInfo or None
    """
    modal_token = None
    verb_token = None

    if target.pos_ == "VERB" and "VerbForm=Inf" in target.morph:
        head = target.head
        if head != target and (head.tag_ == "VMFIN" or head.lemma_ in GERMAN_MODALS):
            if _are_syntactically_related(head, target):
                modal_token = head
                verb_token = target
                selected = "verb"
    elif target.tag_ == "VMFIN" or target.lemma_ in GERMAN_MODALS:
        modal_token = target
        lassen_candidate = None
        for t in doc:
            if t == target:
                continue
            if t.pos_ == "VERB" and "VerbForm=Inf" in t.morph:
                if _are_syntactically_related(target, t):
                    if t.lemma_ == "lassen":
                        lassen_candidate = t
                    else:
                        verb_token = t
                        selected = "modal"
                        break
        if verb_token is None and lassen_candidate is not None:
            verb_token = lassen_candidate
            selected = "modal"

    if not modal_token or not verb_token:
        return None

    modal_morph = {}
    for item in modal_token.morph:
        if "=" in item:
            key, val = item.split("=", 1)
            modal_morph[key] = val

    cluster = []
    for t in doc:
        if t == modal_token or t == verb_token:
            continue
        if t.pos_ not in ("VERB", "AUX"):
            continue
        if (t.head == modal_token or t.head == verb_token) and _are_syntactically_related(modal_token, t):
            cluster.append((t.text, t.idx))

    return ModalVerbInfo(
        modal_text=modal_token.text,
        modal_idx=modal_token.idx,
        modal_lemma=modal_token.lemma_,
        modal_morph=modal_morph,
        verb_text=verb_token.text,
        verb_idx=verb_token.idx,
        verb_lemma=simplemma.lemmatize(verb_token.text, lang="de"),
        selected=selected,
        cluster=cluster,
    )


@dataclass
class LassenInfo:
    """Detected lassen + verb construction."""
    verb_infinitive: str       # infinitive of the main verb (e.g., "reparieren")
    lassen_token_text: str     # conjugated form of lassen (e.g., "lässt")
    lassen_token_idx: int      # character offset of lassen in context
    lassen_morph: dict[str, str]  # morphology of lassen
    verb_token_text: str       # the main verb text (e.g., "reparieren")
    verb_token_idx: int        # character offset of the main verb
    has_sich: bool             # whether "sich ... lassen" (passive-reflexive)
    sich_token_text: str | None
    sich_token_idx: int | None


def detect_lassen_construction(
    target, doc: spacy.tokens.Doc
) -> LassenInfo | None:
    """
    Detect verb + lassen constructions.

    Examples:
        "Sie lässt das Auto reparieren" → reparieren lassen (to have sth repaired)
        "Er lässt mich warten" → warten lassen (to make someone wait)
        "Das lässt sich erklären" → sich erklären lassen (can be explained)

    Works when user selects either "lassen" (any form) or the infinitive verb.

    Args:
        target: The resolved spaCy token the user selected
        doc: spaCy Doc of the full context
    """
    # Scope all searches to the sentence containing the selected word
    sent_tokens = list(target.sent) if target.sent else list(doc)

    lassen_token = None
    verb_token = None

    if target.lemma_ == "lassen" or target.text.lower() in ("lassen", "lässt", "lass", "lasst", "ließ", "ließen", "ließt", "ließest"):
        # User selected a form of "lassen" — find the infinitive it governs
        lassen_token = target
        # Look for an infinitive verb that is syntactically related
        for t in sent_tokens:
            if t == target:
                continue
            if t.pos_ == "VERB" and t.morph.get("VerbForm") == "Inf":
                if _are_syntactically_related(lassen_token, t):
                    verb_token = t
                    break
        # Also check for verbs headed by lassen (dependency child)
        if not verb_token:
            for t in sent_tokens:
                if t == target:
                    continue
                if t.pos_ == "VERB" and (t.head == lassen_token or lassen_token.head == t):
                    verb_token = t
                    break
    elif target.pos_ == "VERB":
        # User selected a verb — check if "lassen" is in the sentence and related
        for t in sent_tokens:
            if t.lemma_ == "lassen" and t != target:
                if _are_syntactically_related(t, target):
                    lassen_token = t
                    verb_token = target
                    break

    if not lassen_token or not verb_token:
        return None

    # Parse lassen morphology
    lassen_morph = {}
    for item in lassen_token.morph:
        if "=" in item:
            key, val = item.split("=", 1)
            lassen_morph[key] = val

    # Get the main verb infinitive
    verb_infinitive = simplemma.lemmatize(verb_token.text, lang="de")

    # Check for reflexive "sich ... lassen" within the same sentence
    sich_token = None
    for t in sent_tokens:
        if t.text.lower() == "sich":
            sich_token = t
            break

    return LassenInfo(
        verb_infinitive=verb_infinitive,
        lassen_token_text=lassen_token.text,
        lassen_token_idx=lassen_token.idx,
        lassen_morph=lassen_morph,
        verb_token_text=verb_token.text,
        verb_token_idx=verb_token.idx,
        has_sich=sich_token is not None,
        sich_token_text=sich_token.text if sich_token else None,
        sich_token_idx=sich_token.idx if sich_token else None,
    )

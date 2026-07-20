from prompts.context_translation import build_context_translation_instruction


POS_MAP = {
    "DET": "determiner/article",
    "PRON": "pronoun",
    "VERB": "verb",
    "NOUN": "noun",
    "ADJ": "adjective",
    "ADV": "adverb",
    "ADP": "preposition",
    "CONJ": "conjunction",
    "CCONJ": "coordinating conjunction",
    "SCONJ": "subordinating conjunction",
    "PART": "particle",
    "NUM": "numeral",
    "INTJ": "interjection",
}


def _pos_instruction(word: str, pos: str | None) -> str:
    if pos and pos in POS_MAP:
        return f'The word "{word}" is a {POS_MAP[pos]}. '
    return ""


def _context_clause(context: str, pos_instruction: str) -> str:
    if context:
        return f'{pos_instruction}The word appears in this sentence: "{context}"'
    if pos_instruction:
        return pos_instruction.rstrip()
    return ""


def _collocation_clause(collocation_pattern: str | None, target_lang: str) -> str:
    if not collocation_pattern:
        return ""
    return f"""
CRITICAL: The word is part of the verb+preposition collocation "{collocation_pattern}".
You must translate the COLLOCATION as a whole, giving the natural IDIOMATIC equivalent in {target_lang} — NOT a word-for-word literal translation.
Examples of correct idiomatic translations:
- "von etwas ausgehen" → French: "partir du principe que / supposer / estimer" (NOT "partir de")
- "von jemandem etwas erwarten" → French: "s'attendre à quelque chose de la part de quelqu'un" (NOT "prévoir" or "attendre")
- "auf etwas ankommen" → French: "dépendre de" (NOT "arriver sur")
Apply the same principle: find the natural {target_lang} expression that carries the same meaning as the source-language collocation.
The context_translation MUST also use this idiomatic equivalent, not a literal rendering."""


def _lemma_clause(word: str, lemma: str | None) -> str:
    if lemma and lemma != word:
        return f'\nAlso translate the base form (infinitive) "{lemma}" separately. Give the correct, natural dictionary translation — not a transliteration or invented word.'
    return ""


def _modal_clause(modal_verb: str | None) -> str:
    if modal_verb:
        return f'\nAlso translate the modal verb "{modal_verb}" as used in the context sentence. Give the conjugated translation matching the person/tense in context (e.g., "will" → "veut", "kann" → "peut", "muss" → "doit"), NOT the infinitive.'
    return ""


def _compound_clause(compound_parts: list[str] | None) -> str:
    if not compound_parts:
        return ""
    parts_str = ", ".join(f'"{p}"' for p in compound_parts)
    return f'\nThese are the EXACT compound word parts (do NOT split them further): {parts_str}. For each part, find its dictionary form and translate it. Keep nouns as nouns (e.g., "Gesundheit" stays "Gesundheit", not "gesund"). Only simplify declined/genitive forms (e.g., "Auslands" → "Ausland", "Kranken" → "krank"). Return exactly {len(compound_parts)} parts.'


def _translation_field(target_lang: str, collocation_pattern: str | None) -> str:
    if collocation_pattern:
        return f"the idiomatic translation of the COLLOCATION in {target_lang} (e.g., the full verbal phrase like 's''attendre à')"
    return f"the SHORT, CONCISE dictionary translation of the word itself in {target_lang} — 1 to 4 words maximum, like a dictionary entry (e.g. 'être disponible', 'partir', 'maison'). Do NOT use the context sentence to build a phrase. Translate the WORD, not the sentence."


def _modal_field(modal_verb: str | None) -> str:
    if not modal_verb:
        return ""
    return f'\n- modal_translation: conjugated translation of "{modal_verb}" matching the person/tense in context (e.g., "will" → "veut", "kann" → "peut", "muss" → "doit"). NEVER give the infinitive form.'


def _compound_field(compound_parts: list[str] | None) -> str:
    if not compound_parts:
        return ""
    return '\n- parts: array of objects with "part" (original), "base" (lemma/base form), and "translation" (translation of base form) for each compound part (only if compound parts were provided)'


def build_word_translation_prompt(
    word: str,
    source_lang: str,
    target_lang: str,
    context: str = "",
    lemma: str | None = None,
    skip_context_translation: bool = False,
    compound_parts: list[str] | None = None,
    collocation_pattern: str | None = None,
    modal_verb: str | None = None,
    pos: str | None = None,
) -> str:
    pos_instruction = _pos_instruction(word, pos)
    context_instruction = _context_clause(context, pos_instruction)
    collocation_instruction = _collocation_clause(collocation_pattern, target_lang)
    lemma_instruction = _lemma_clause(word, lemma)
    modal_instruction = _modal_clause(modal_verb)
    compound_instruction = _compound_clause(compound_parts)
    context_translation_instruction = (
        ""
        if skip_context_translation
        else build_context_translation_instruction(source_lang, target_lang)
    )

    return f"""Translate "{word}" from {source_lang} to {target_lang}.
{context_instruction}
{collocation_instruction}
{lemma_instruction}
{modal_instruction}
{compound_instruction}

Return JSON with:
- translation: {_translation_field(target_lang, collocation_pattern)}
- meaning: one sentence in {target_lang} explaining what "{word}" means IN THIS SPECIFIC CONTEXT (use the context sentence to explain, but keep it concise)
- base_translation: translation of the base form "{lemma}" (only if base form was provided, otherwise null){context_translation_instruction}{_modal_field(modal_verb)}{_compound_field(compound_parts)}

Return ONLY valid JSON. Do not use guillemets (« »), curly quotes, or any special punctuation inside JSON string values — use only plain straight quotes for quoting words within strings."""


def build_simple_translation_prompt(word: str, source_lang: str, target_lang: str) -> str:
    return f"""Translate {word} from {source_lang} to {target_lang}. Return ONLY the translation, nothing else.

{word}

Return JSON with:
- translation: the equivalent word/phrase in {target_lang}

Return ONLY valid JSON. Do not use guillemets (« »), curly quotes, or any special punctuation inside JSON string values — use only plain straight quotes for quoting words within strings."""

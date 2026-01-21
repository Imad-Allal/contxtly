from groq import Groq

from config import settings

client = Groq(api_key=settings.groq_api_key)

SIMPLE_PROMPT = """Translate to {target_lang}. Return ONLY the translation.

{text}"""

SMART_PROMPT = """Translate "{text}" from {source_lang} to {target_lang}.
Context: "{context}"

Rules:
- Example: write in {source_lang}
- Meaning: write in {target_lang}
- Breakdown: ONLY include if the word has multiple meaningful parts:
  - Compound words: "Falschbehauptungen" → "Falsch (false) + Behauptungen (claims)"
  - Conjugated verbs: "wärmte" → "wärm- (to warm) + -te (past tense)"
  - Plurals/cases: "Häuser" → "Haus (house) + -er (plural)"
  - If the word is simple (like "Rede", "Haus", "gut"), DO NOT include Breakdown line at all

Format (follow exactly):

**Translation**: [translation in {target_lang}]
**Meaning**: [one short sentence in {target_lang} explaining the meaning]
**Breakdown**: [part1 (meaning) + part2 (meaning) in {target_lang}] OR omit this line entirely
**Example**:
- [example in {source_lang}]
- [translation in {target_lang}]
"""


def translate_simple(
    text: str,
    source_lang: str,
    target_lang: str,
) -> str:
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": SIMPLE_PROMPT.format(
                    text=text,
                    source_lang=source_lang,
                    target_lang=target_lang,
                ),
            }
        ],
        temperature=0.1,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def translate_smart(
    text: str,
    context: str,
    source_lang: str,
    target_lang: str,
) -> str:
    """Detailed translation with examples and grammar notes."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": SMART_PROMPT.format(
                    text=text,
                    context=context or "No context provided",
                    source_lang=source_lang,
                    target_lang=target_lang,
                ),
            }
        ],
        temperature=0.3,
        max_tokens=500,
    )
    return response.choices[0].message.content.strip()

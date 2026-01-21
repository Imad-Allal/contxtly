from groq import Groq

from config import settings

client = Groq(api_key=settings.groq_api_key)

SIMPLE_PROMPT = """Translate the following text from {source_lang} to {target_lang}.
Return ONLY the translation, nothing else.

Text: {text}"""

SMART_PROMPT = """Translate "{text}" from {source_lang} to {target_lang}.
Context: "{context}"

Respond in this exact format, nothing else:

**Translation**: [translation]
**Meaning**: [one sentence max]
**Examples**:
- [example 1 in {target_lang}]
- [example 2 in {target_lang}]
**Grammar**: [one sentence max, only if relevant]"""


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

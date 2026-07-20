LANG_NAMES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "zh": "Chinese", "ja": "Japanese",
    "ko": "Korean", "ar": "Arabic", "ru": "Russian",
}


STYLE_NOTES: dict[str, str] = {
    "fr": (
        "Use natural French phrasing. Avoid literal calques of source-language constructions. "
        "Drop redundant adverbs that sound heavy in French. Use elision and standard punctuation. "
        "Favour idiomatic connectors and natural word order over surface-level mirroring of the source."
    ),
    "en": (
        "Use natural, conversational English unless the source register is formal. "
        "Avoid mirroring source-language word order. Drop or render modal particles through tone and word choice. "
        "Contract where natural in casual contexts. Prefer plain English over Latinate calques."
    ),
    "es": (
        "Use natural Spanish. Avoid literal calques. Render source-language modal particles through tone or omit them. "
        "Distinguish ser/estar correctly; respect tú/usted register inferred from the source."
    ),
    "it": (
        "Use natural Italian. Avoid literal calques. "
        "Use elision and apostrophes correctly; favour idiomatic word order over mirroring the source."
    ),
    "pt": (
        "Use natural Portuguese. Avoid literal calques. "
        "Default to Brazilian Portuguese unless the source register or vocabulary clearly suggests European."
    ),
    "de": (
        "Use natural German. Maintain V2 word order in main clauses, verb-final in subordinate clauses. "
        "Use modal particles where they would feel natural. Choose register (du/Sie) based on cues in the source."
    ),
    "zh": (
        "Use natural Mandarin Chinese (Simplified). Avoid Indo-European sentence structures. "
        "Drop articles and explicit subjects where Chinese would; use measure words correctly."
    ),
    "ja": (
        "Use natural Japanese. Match the register of the source: です/ます for neutral/polite contexts, plain form for casual. "
        "Drop subjects where Japanese would. Use particles (は/が/を/に/で) correctly; do not literally translate source articles."
    ),
    "ko": (
        "Use natural Korean. Match the register of the source: 합니다체 for formal, 해요체 for polite, 해체 for casual. "
        "Drop subjects where Korean would. Use particles (은/는/이/가/을/를) correctly; respect honorifics inferred from context."
    ),
    "ar": (
        "Use Modern Standard Arabic unless the source register clearly suggests dialect. "
        "Avoid literal calques. Use correct gender/number agreement; respect natural VSO or SVO ordering as appropriate."
    ),
    "ru": (
        "Use natural Russian. Avoid literal calques. "
        "Use correct case endings; choose perfective/imperfective aspect based on source meaning. Use natural word order."
    ),
}


EXAMPLES: dict[tuple[str, str], list[dict]] = {
    ("de", "fr"): [
        {
            "source": "Es kommt darauf an, was du willst.",
            "bad":    "Cela vient sur cela ce que tu veux.",
            "good":   "Ça dépend de ce que tu veux.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "Je pars de cela qu'il vient.",
            "good":   "Je pars du principe qu'il viendra.",
        },
        {
            "source": "Teils so, teils so.",
            "bad":    "En partie ainsi, en partie ainsi.",
            "good":   "Tantôt l'un, tantôt l'autre.",
        },
    ],
    ("de", "en"): [
        {
            "source": "Es kommt darauf an, was du willst.",
            "bad":    "It comes on it what you want.",
            "good":   "It depends on what you want.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "I go out from that, that he comes.",
            "good":   "I assume he'll come.",
        },
        {
            "source": "Das ist halt so.",
            "bad":    "That is just so.",
            "good":   "That's just how it is.",
        },
    ],
    ("de", "es"): [
        {
            "source": "Es kommt darauf an.",
            "bad":    "Viene sobre eso.",
            "good":   "Depende.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "Yo voy de eso fuera, que él viene.",
            "good":   "Doy por hecho que vendrá.",
        },
        {
            "source": "Das ist halt so.",
            "bad":    "Eso es simplemente así.",
            "good":   "Es lo que hay.",
        },
    ],
    ("de", "it"): [
        {
            "source": "Es kommt darauf an.",
            "bad":    "Viene su quello.",
            "good":   "Dipende.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "Io vado da ciò fuori che lui viene.",
            "good":   "Do per scontato che verrà.",
        },
    ],
    ("de", "pt"): [
        {
            "source": "Es kommt darauf an.",
            "bad":    "Vem sobre isso.",
            "good":   "Depende.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "Eu vou disso fora, que ele vem.",
            "good":   "Parto do princípio de que ele virá.",
        },
    ],
    ("de", "zh"): [
        {
            "source": "Es kommt darauf an, was du willst.",
            "bad":    "它来在上面那个，你想要什么。",
            "good":   "这要看你想要什么。",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "我从此出发，他来。",
            "good":   "我认为他会来。",
        },
    ],
    ("de", "ja"): [
        {
            "source": "Es kommt darauf an, was du willst.",
            "bad":    "それはその上に来る、あなたが何を欲しいか。",
            "good":   "君が何を望むかによるよ。",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "私はそれから出発する、彼が来ることを。",
            "good":   "彼は来ると思っている。",
        },
    ],
    ("de", "ko"): [
        {
            "source": "Es kommt darauf an, was du willst.",
            "bad":    "그것은 그 위에 온다, 네가 무엇을 원하는지.",
            "good":   "네가 뭘 원하는지에 달려 있어.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "나는 그것에서 나간다, 그가 온다고.",
            "good":   "그가 올 거라고 생각해.",
        },
    ],
    ("de", "ar"): [
        {
            "source": "Es kommt darauf an, was du willst.",
            "bad":    "هو يأتي على ذلك، ماذا أنت تريد.",
            "good":   "هذا يتوقف على ما تريده.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "أذهب من ذلك خارجاً أنه يأتي.",
            "good":   "أفترض أنه سيأتي.",
        },
    ],
    ("de", "ru"): [
        {
            "source": "Es kommt darauf an, was du willst.",
            "bad":    "Это приходит на то, что ты хочешь.",
            "good":   "Это зависит от того, чего ты хочешь.",
        },
        {
            "source": "Ich gehe davon aus, dass er kommt.",
            "bad":    "Я иду от этого, что он приходит.",
            "good":   "Я исхожу из того, что он придёт.",
        },
    ],
}


def build_context_translation_instruction(source_lang: str, target_lang: str) -> str:
    """
    Build the JSON-field instruction for context_translation, including
    target-specific style notes and BAD/GOOD reference examples.
    """
    target_name = LANG_NAMES.get(target_lang, target_lang)
    style_note = STYLE_NOTES.get(target_lang, "")
    examples = EXAMPLES.get((source_lang, target_lang), [])

    parts = [
        f"\n- context_translation: render the full context sentence in natural, native-sounding {target_name} "
        f"as a fluent native speaker would actually say it — NOT a word-for-word translation. "
        f"Preserve meaning, tone, and register, but restructure phrasing freely (reorder clauses, drop awkward "
        f"fillers, use idiomatic equivalents) so it reads as if originally written in {target_name}. "
        f"Avoid literal calques of source-language constructions. MUST be in {target_name}, NOT the original "
        f"source text. Return ONLY the rendered sentence as a plain string — no quotes, no explanations, no "
        f"original text. If context was not provided, use null."
    ]

    if style_note:
        parts.append(f"\n\n{target_name} style guidance: {style_note}")

    if examples:
        parts.append("\n\nReference examples (apply the same standard to the actual sentence):")
        for ex in examples:
            parts.append(
                f"\n- Source: \"{ex['source']}\""
                f"\n  BAD (literal): \"{ex['bad']}\""
                f"\n  GOOD (idiomatic): \"{ex['good']}\""
            )

    return "".join(parts)

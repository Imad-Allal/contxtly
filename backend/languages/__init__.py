from languages.base import LanguageConfig, LanguageModule, LanguageAnalysis, describe_morphology

# German module: pick v1 or v2 based on the GERMAN_V2_ENABLED env flag.
# Both modules share the same dict_store and detector functions.
try:
    from config import settings
    _german_v2 = settings.german_v2_enabled
except Exception:
    _german_v2 = False

if _german_v2:
    from languages.german_v2 import German
else:
    from languages.german import German


# Registry of all supported languages
_LANGUAGES: dict[str, LanguageModule] = {
    "de": German(),
    # "fr": French(),
    # "en": English(),
}


def get_language(code: str) -> LanguageModule | None:
    """Get language module by ISO 639-1 code."""
    return _LANGUAGES.get(code)


def get_config(code: str) -> LanguageConfig | None:
    """Get language configuration by ISO 639-1 code."""
    lang = get_language(code)
    return lang.config if lang else None


def get_spacy_models() -> dict[str, str]:
    """Get mapping of language codes to spaCy model names."""
    return {code: lang.config.spacy_model for code, lang in _LANGUAGES.items()}


def supported_languages() -> list[str]:
    """Get list of supported language codes."""
    return list(_LANGUAGES.keys())


__all__ = [
    "LanguageConfig",
    "LanguageModule",
    "LanguageAnalysis",
    "describe_morphology",
    "get_language",
    "get_config",
    "get_spacy_models",
    "supported_languages",
]

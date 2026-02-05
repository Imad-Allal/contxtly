from languages.base import LanguageConfig, LanguageModule, LanguageAnalysis, describe_morphology
from languages.german import German
from languages.french import French
from languages.english import English


# Registry of all supported languages
_LANGUAGES: dict[str, LanguageModule] = {
    "de": German(),
    "fr": French(),
    "en": English(),
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

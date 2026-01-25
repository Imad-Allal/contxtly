"""Portuguese language configuration."""

from languages.base import LanguageConfig, LanguageModule


class Portuguese(LanguageModule):
    """Portuguese language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="pt",
            name="Portuguese",
            spacy_model="pt_core_news_sm",
        )

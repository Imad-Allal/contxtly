"""Italian language configuration."""

from languages.base import LanguageConfig, LanguageModule


class Italian(LanguageModule):
    """Italian language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="it",
            name="Italian",
            spacy_model="it_core_news_sm",
        )

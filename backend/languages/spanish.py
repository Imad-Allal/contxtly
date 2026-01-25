"""Spanish language configuration."""

from languages.base import LanguageConfig, LanguageModule


class Spanish(LanguageModule):
    """Spanish language support."""

    @property
    def config(self) -> LanguageConfig:
        return LanguageConfig(
            code="es",
            name="Spanish",
            spacy_model="es_core_news_sm",
        )

import sys
import os
import pytest

# Add backend to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from analyzer import get_model


@pytest.fixture(scope="session", autouse=True)
def preload_spacy():
    """Load the German spaCy model once for all tests."""
    model = get_model("de")
    assert model is not None, "German spaCy model (de_core_news_lg) not installed"
    return model

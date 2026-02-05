from dataclasses import dataclass


@dataclass
class TokenRef:
    """Reference to a token in context (text + character offset)."""
    text: str
    offset: int

    def to_dict(self) -> dict:
        return {"text": self.text, "offset": self.offset}

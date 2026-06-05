from dataclasses import dataclass

@dataclass
class Variant:
    code: str
    name: str
    min: str
    medium: str
    max: str

@dataclass
class Card:
    name: str
    rarity: str
    variants: list[Variant]

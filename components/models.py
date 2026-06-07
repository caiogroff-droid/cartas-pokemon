from dataclasses import dataclass

@dataclass
class Variant:
    code: str
    name: str
    min: str
    medium: str
    max: str
    favorite: bool
    prices_per_state: dict[str, str]


@dataclass
class Cards:
    link: str
    name: str
    rarity: str
    variants: list[Variant]

@dataclass
class CardState:
    name: str
    rarity: str
    prices: dict[str, str] | None
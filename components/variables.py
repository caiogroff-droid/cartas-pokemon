


from enum import Enum

from models import Cards


cartas: dict[str, Cards] = {}
loading: bool = False

class FilterType(Enum):
    OWNED = 1
    NOT_OWNED = 2
    HAS_PRICE_DATA = 3
    ALL = 0
    
currentfilterType = FilterType.ALL
lastSearch: str = ''
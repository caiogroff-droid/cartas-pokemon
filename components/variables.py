


from enum import Enum

from models import Cards


cartas: dict[str, Cards] = {}

class FilterType(Enum):
    OWNED = 1
    ALL = 0
    
currentfilterType = FilterType.ALL
lastSearch: str = ''
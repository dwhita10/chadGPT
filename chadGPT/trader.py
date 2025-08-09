from abc import ABC, abstractmethod
from datetime import datetime

from chadGPT.data_models import Trade, Rule, Position, Portfolio

# generic trade model
class BaseBroker(ABC):
    @abstractmethod
    def create_order(self, trade: Trade):
        pass

    @abstractmethod
    def get_portfolio(self) -> Portfolio:
        pass
        

class MarketResearch(ABC):
    @abstractmethod
    def get_current_value(symbol: str):
        pass
    
    @abstractmethod
    def get_historic_value(symbol: str, start: datetime, end: datetime, aggregation: str):
        pass

# TODO: Alpaca-Py Implementation https://alpaca.markets/sdks/python/getting_started.html

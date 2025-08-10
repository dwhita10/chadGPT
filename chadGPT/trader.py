from abc import ABC, abstractmethod
from datetime import datetime

from chadGPT.data_models import (
    TradeOrder, Rule, Position, Portfolio,
    Stock, StockBar
)

# generic trade model
class BaseBroker(ABC):
    @abstractmethod
    def create_order(self, trade: TradeOrder):
        pass

    @abstractmethod
    def get_portfolio(self) -> Portfolio:
        pass
        

class BaseMarketResearch(ABC):
    @abstractmethod
    def get_current_value(symbol: str) -> Stock:
        pass
    
    @abstractmethod
    def get_historic_value(symbol: str, start: datetime, end: datetime, aggregation: str) -> list[StockBar]:
        pass


def make_trades_from_portfolio(
    current_portfolio: Portfolio,
    desired_portfolio: Portfolio
) -> list[TradeOrder]:
    pass


# TODO: Alpaca-Py Implementation https://alpaca.markets/sdks/python/getting_started.html

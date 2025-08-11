from abc import ABC, abstractmethod
from datetime import datetime

from chadGPT.data_models import (
    TradeOrder, Rule, Position, Portfolio, DesiredPortfolio,
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
    desired_portfolio: DesiredPortfolio
) -> list[TradeOrder]:
    trade_orders = []
    current_positions = {p.symbol: p for p in current_portfolio.positions}
    desired_positions = {p.symbol: p for p in desired_portfolio.positions}

    # Handle buys and adjustments
    for symbol, desired_pos in desired_positions.items():
        current_pos = current_positions.get(symbol)
        desired_amount = desired_pos.amount
        if current_pos is None or not current_pos.shares:
            # New position, buy full desired amount
            trade_orders.append(
                TradeOrder(
                    type='buy',
                    symbol=symbol,
                    amount=desired_amount,
                    trade_time=None,
                    rules=[]
                )
            )
        else:
            current_amount = current_pos.shares
            diff = desired_amount - current_amount
            if diff > 0:
                trade_orders.append(
                    TradeOrder(
                        type='buy',
                        symbol=symbol,
                        amount=diff,
                        trade_time=None,
                        rules=current_pos.rules
                    )
                )
            elif diff < 0:
                trade_orders.append(
                    TradeOrder(
                        type='sell',
                        symbol=symbol,
                        amount=abs(diff),
                        trade_time=None,
                        rules=current_pos.rules
                    )
                )

    # Handle sells for positions not in desired portfolio
    for symbol, current_pos in current_positions.items():
        if symbol not in desired_positions:
            if current_pos.shares and current_pos.shares > 0:
                trade_orders.append(
                    TradeOrder(
                        type='sell',
                        symbol=symbol,
                        amount=current_pos.shares,
                        trade_time=None,
                        rules=current_pos.rules
                    )
                )

    return trade_orders


# TODO: Alpaca-Py Implementation https://alpaca.markets/sdks/python/getting_started.html

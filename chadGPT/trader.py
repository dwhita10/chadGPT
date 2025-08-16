from abc import ABC, abstractmethod
from datetime import datetime, timezone

from chadGPT.data_models import (
    TradeOrder, Rule, Position, Portfolio, RelativePortfolio,
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
    desired_portfolio: RelativePortfolio
) -> list[TradeOrder]:
    """
    Compare current portfolio to desired portfolio and generate TradeOrders
    to rebalance positions.
    """
    trades: list[TradeOrder] = []

    # Build lookup for current positions
    current_positions = {pos.symbol: pos for pos in current_portfolio.positions}
    total_value = current_portfolio.total_value

    # Build lookup for desired positions
    desired_positions = {pos.symbol: pos for pos in desired_portfolio.positions}

    # Process sells and adjustments
    for symbol, pos in current_positions.items():
        desired = desired_positions.get(symbol)
        if not desired:
            # Sell entire position if not in desired portfolio
            trades.append(TradeOrder(
                type='sell',
                symbol=symbol,
                amount=pos.shares,
                trade_time=None,
                rules=pos.rules
            ))
        else:
            # Adjust position if needed
            desired_amount = (desired.percent_of_portfolio * total_value) / pos.value * pos.shares if pos.value > 0 else 0
            diff = desired_amount - pos.shares
            if abs(diff) > 1e-6:
                trade_type = 'buy' if diff > 0 else 'sell'
                trades.append(TradeOrder(
                    type=trade_type,
                    symbol=symbol,
                    amount=abs(diff),
                    trade_time=None,
                    rules=desired.rules or pos.rules
                ))

    # Process buys for new positions
    for symbol, desired in desired_positions.items():
        if symbol not in current_positions:
            # Buy new position
            amount = (desired.percent_of_portfolio * total_value) / desired_portfolio.cash if desired_portfolio.cash > 0 else 0
            trades.append(TradeOrder(
                type='buy',
                symbol=symbol,
                amount=amount,
                trade_time=None,
                rules=desired.rules or Rule()
            ))

    return trades

# testing implementation

class FakeBroker(BaseBroker):
    def create_order(self, trade: TradeOrder):
        print(f"Executing trade: {trade.type} {trade.amount} of {trade.symbol}")
    
    def get_portfolio(self) -> Portfolio:
        # return a dummy portfolio for testing
        return Portfolio(
            total_value=100.0,
            cash=100.0,
            positions=[
            ],
            timestamp=datetime.now(timezone.utc)
        )
    
class FakeMarketResearch(BaseMarketResearch):
    def get_current_value(self, symbol: str) -> Stock:
        return Stock(
            symbol=symbol,
            price=100.0,
            time=datetime.now()
        )
    
    def get_historic_value(self, symbol: str, start: datetime, end: datetime, aggregation: str) -> list[StockBar]:
        return [
            StockBar(
                symbol=symbol,
                time=start,
                open=100.0,
                high=110.0,
                low=90.0,
                close=105.0,
                volume=1000,
                trade_count=10,
                volume_weighted_avg_price=102.0
            ),
            StockBar(
                symbol=symbol,
                time=end,
                open=105.0,
                high=115.0,
                low=95.0,
                close=110.0,
                volume=1500,
                trade_count=15,
                volume_weighted_avg_price=108.0
            )
        ]

# TODO: Alpaca-Py Implementation https://alpaca.markets/sdks/python/getting_started.html

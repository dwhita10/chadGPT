from typing import Optional, Callable, Type, Literal

from datetime import datetime
from pydantic import BaseModel


# giga related data models (user preferences)
class Preferences(BaseModel):
    research_prompt: str | None = None
    portfolio_update_prompt: str | None = None
    portfolio_update_frequency: Literal['hourly', 'daily', 'weekly'] = 'daily'
    strategy_update_frequency: Literal['daily', 'weekly', 'monthly'] = 'weekly'
    max_take_profit_percent: float = 0.15
    max_stop_loss_percent: float = 0.10
    max_portfolio_size: int = 15
    trade_type: Literal['paper', 'live'] = 'paper'


# brain related data models (LLM)
class LLMRequest(BaseModel):
    prompt: str
    background: Optional[str]
    context: Optional[list[BaseModel] | str]
    expected_format: Optional[Type[BaseModel]]


class StrategyResponse(BaseModel):
    strategy_report: str
    stock_symbols_to_watch: list[str]


# Orchestrator related data models
class Task(BaseModel):
    func: Callable # output should be a tuple
    args: tuple


class Job(BaseModel):
    schedule: str # cron schedule syntax see https://crontab.guru/
    tasks: list[Task] # each sequential task should be unloaded into the next


# trade related data models
class Rule(BaseModel):
    stop_loss_pct: Optional[float]
    take_profit_pct: Optional[float]


class Stock(BaseModel):
    symbol: str
    price: float
    time: Optional[datetime]


class StockBar(BaseModel):
    symbol: str
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    trade_count: int
    volume_weighted_avg_price: float


class TradeOrder(BaseModel):
    type: Literal['buy', 'sell']
    symbol: str
    amount: float
    trade_time: Optional[datetime]
    rules: Rule


class Position(BaseModel):
    symbol: str
    shares: float
    rules: Rule
    value: float
    

class Portfolio(BaseModel):
    positions: list[Position]
    cash: float
    total_value: float
    timestamp: datetime


class RelativePosition(BaseModel):
    symbol: str
    percent_of_portfolio: float
    rules: Rule


class RelativePortfolio(BaseModel):
    positions: list[RelativePosition]
    percent_cash: float

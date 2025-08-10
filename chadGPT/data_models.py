from typing import Optional, Callable, Type, Literal

from datetime import datetime
from pydantic import BaseModel


# brain related data models (LLM)
class LLMRequest(BaseModel):
    prompt: str
    background: Optional[str]
    context: Optional[list[BaseModel | str]]
    expected_format: Optional[Type[BaseModel]]


# Orchestrator related data models
class Task(BaseModel):
    func: Callable # output should be a tuple
    args: tuple


class Job(BaseModel):
    schedule: str # cron schedule syntax see https://crontab.guru/
    tasks: list[Task] # each sequential task should be unloaded into the next


# trade related data models
class Rule(BaseModel):
    stop_loss: Optional[float]
    take_profit: Optional[float]
    sell_date: Optional[datetime]


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
    rules: list[Rule]


class Position(BaseModel):
    symbol: str
    shares: float | None
    rules: list[Rule]
    value: Optional[float]
    

class Portfolio(BaseModel):
    positions: list[Position]
    cash: float


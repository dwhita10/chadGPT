from typing import Optional, Callable, Type

from datetime import datetime
from pydantic import BaseModel


# brain related data models (LLM)
class LLMRequest(BaseModel):
    prompt: str
    background: Optional[str]
    context: Optional[list[BaseModel | str]]
    expected_format: Optional[Type[BaseModel]]


# giga (orchestrator) related data models
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


class Trade(BaseModel):
    symbol: str
    amount: float
    trade_time: Optional[datetime]
    rules: list[Rule]


class Position(BaseModel):
    symbol: str
    shares: float
    value: Optional[float]
    rules: list[Rule]


class Portfolio(BaseModel):
    positions: list[Position]
    cash: float


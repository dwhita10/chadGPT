from typing import Optional

from datetime import datetime
from pydantic import BaseModel


# giga (orchestrator) related data models



# trade related data models

class Trade(BaseModel):
    symbol: str
    amount: float
    trade_time: Optional[datetime]
    

class Position(BaseModel):
    symbol: str
    shares: float
    value: Optional[float]


class Portfolio(BaseModel):
    positions: list[Position]


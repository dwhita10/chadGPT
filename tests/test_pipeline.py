import os
import sys
# add the parent directory to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from datetime import datetime, timezone
from typing import Any
from chadGPT.giga import Giga
from chadGPT.trader import BaseBroker, BaseMarketResearch
from chadGPT.brain import BaseLLM
from chadGPT.db import SQLiteDatabase

from chadGPT.data_models import (
    Preferences, StrategyResponse, RelativePortfolio, Portfolio, Position, Rule,
    Task, Job, LLMRequest, RelativePosition
)

# ---- Fixtures ----

class DummyLLM(BaseLLM):
    def __init__(self):
        self.last_request = None

    def submit_query(self, query: str) -> str:
        # Always return a valid JSON for the expected format
        if "StrategyResponse" in query:
            return '{"strategy_report": "Test strategy", "stock_symbols_to_watch": ["AAPL", "GOOGL"]}'
        elif "RelativePortfolio" in query:
            return '{"positions": [{"symbol": "AAPL", "percent_of_portfolio": 0.5, "rules": {"stop_loss_pct": 0.1, "take_profit_pct": 0.2}}, {"symbol": "GOOGL", "percent_of_portfolio": 0.5, "rules": {"stop_loss_pct": 0.1, "take_profit_pct": 0.2}}], "percent_cash": 0.0}'
        return '{}'

class DummyBroker(BaseBroker):
    def __init__(self):
        self.orders = []
        self._portfolio = Portfolio(
            positions=[
                Position(symbol="AAPL", shares=10, value=1500.0, rules=Rule(stop_loss_pct=0.1, take_profit_pct=0.2)),
                Position(symbol="GOOGL", shares=5, value=2000.0, rules=Rule(stop_loss_pct=0.1, take_profit_pct=0.2)),
            ],
            cash=1000.0,
            total_value=4500.0,
            timestamp=datetime.now(timezone.utc)
        )

    def create_order(self, trade):
        self.orders.append(trade)

    def get_portfolio(self):
        return self._portfolio

class DummyMarket(BaseMarketResearch):
    def get_current_value(self, symbol: str):
        return None

    def get_historic_value(self, symbol: str, start: datetime, end: datetime, aggregation: str):
        return []



@pytest.fixture(scope="module")
def dummy_llm():
    return DummyLLM()

@pytest.fixture(scope="module")
def dummy_broker():
    return DummyBroker()

@pytest.fixture(scope="module")
def dummy_market():
    return DummyMarket()

@pytest.fixture(scope="module")
def dummy_db():
    db = SQLiteDatabase("sqlite:///data/test.db")
    yield db
    # cleanup
    db.engine.dispose()
    os.remove("data/test.db")

@pytest.fixture(scope="module")
def giga(dummy_broker, dummy_market, dummy_llm, dummy_db):
    prefs = Preferences()
    return Giga(
        broker=dummy_broker,
        market=dummy_market,
        portfolio_update_brain=dummy_llm,
        research_brain=dummy_llm,
        user_preferences=prefs,
        db=dummy_db,
        user="test_user"
    )

# ---- Tests ----

def test_generate_strategy(giga):
    strategy = giga.generate_strategy()
    assert isinstance(strategy, StrategyResponse)
    assert strategy.strategy_report == "Test strategy"
    assert "AAPL" in strategy.stock_symbols_to_watch

def test_get_portfolio_updates(giga):
    strategy = StrategyResponse(strategy_report="Test", stock_symbols_to_watch=["AAPL", "GOOGL"])
    rel_portfolio = giga.get_portfolio_updates(strategy=strategy)
    assert isinstance(rel_portfolio, RelativePortfolio)
    assert len(rel_portfolio.positions) == 2
    assert rel_portfolio.positions[0].symbol == "AAPL"

def test_giga_pipeline(giga):
    strategy, trades = giga.giga_pipeline()
    assert isinstance(strategy, StrategyResponse)
    assert isinstance(trades, list)
    # Trades should be generated for rebalancing
    assert all(hasattr(trade, "symbol") for trade in trades)

def test_update_portfolio_pipeline(giga):
    trades = giga.update_portfolio_pipeline()
    assert isinstance(trades, list)
    assert all(hasattr(trade, "symbol") for trade in trades)

def test_create_jobs(giga):
    jobs = giga.create_jobs()
    assert isinstance(jobs, list)
    assert all(isinstance(job, Job) for job in jobs)
    assert any(job.tasks for job in jobs)
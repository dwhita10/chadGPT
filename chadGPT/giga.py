from pydantic import BaseModel
from datetime import datetime, timezone, timedelta

from chadGPT.data_models import (
    Job, Task, LLMRequest
)
from chadGPT.brain import BaseLLM, apply_delimiter
from chadGPT.data_models import Preferences, StrategyResponse, RelativePortfolio, Portfolio
from chadGPT.trader import BaseBroker, BaseMarketResearch
from chadGPT.db import BaseDatabase, SQLiteDatabase

# general workflow
# 1. Strategy Generation/Update (frequency)
# 2. Recommend portfolio updates (frequency)
# 3. Implement portfolio update (trades)

class Giga:
    def __init__(
        self, broker: BaseBroker, 
        market: BaseMarketResearch, 
        portfolio_update_brain: BaseLLM,
        research_brain: BaseLLM,
        user_preferences: Preferences = Preferences(),
        db: BaseDatabase = SQLiteDatabase("sqlite:///data/chadGPT.db"),
        user: str = "default_user",
    ):
        self.broker = broker
        self.market = market
        self.portfolio_update_brain = portfolio_update_brain
        self.research_brain = research_brain
        self.user_preferences = user_preferences
        self.db = db
        self.user = user

    def get_previous_strategy(self) -> StrategyResponse | str:
        """
        Retrieve the previous strategy from the database.
        This could be implemented to read from a specific table or log.
        """
        actions = self.db.read(user=self.user, category='strategy')
        if actions:
            strategy = actions[-1].action.get('response', '')
            if isinstance(strategy, dict):
                return StrategyResponse(**strategy)
        return ""
    
    def gather_research_context(self) -> list[BaseModel | str]:
        # gather context such as current portfolio, market data, previous strategies
        context: list[BaseModel | str] = []
        current_portfolio = self.broker.get_portfolio()
        context.append(current_portfolio)
        previous_strategy = BaseLLM.apply_delimiter(
            block_name='previous_strategy', 
            query=self.get_previous_strategy(),
            delimiter_type='caps:'
        )
        context.append(previous_strategy)
        # additional market data could be gathered here as needed
        update_frequency = self.user_preferences.portfolio_update_frequency
        context.append(BaseLLM.apply_delimiter(
            block_name='portfolio_update_frequency',
            query=update_frequency,
            delimiter_type='caps:'
        ))
        strategy_update_frequency = self.user_preferences.strategy_update_frequency
        context.append(BaseLLM.apply_delimiter(
            block_name='strategy_update_frequency',
            query=strategy_update_frequency,
            delimiter_type='caps:'
        ))

        return context

    def gather_portfolio_update_context(
        self, strategy: StrategyResponse | None = None
    ) -> list[BaseModel | str]:
        context = []
        # get previous strategy if not provided
        if strategy is None:
            strategy = self.get_previous_strategy()
        
        stock_symobols_to_watch = []

        # if strategy is a string, it is likely a report or summary
        if isinstance(strategy, str):
            strategy_report = strategy
        # if strategy is a StrategyResponse, extract relevant information
        elif isinstance(strategy, StrategyResponse):
            strategy_report = strategy.strategy_report
            stock_symbols_to_watch = strategy.stock_symbols_to_watch
        # otherwise, attempt to convert to string
        else:
            strategy_report = str(strategy)
        
        context.append(BaseLLM.apply_delimiter(
            block_name='strategy_report',
            query=strategy_report,
            delimiter_type='caps:'
        ))
        
        # get stock symbols from the previous time period
        update_period_dict = {      # key: from preferences portfolio_update_frequency
            'hourly': '1',          # value: number of days to look back
            'daily': '1',
            'weekly': '7'
        }
        timestamp: str = datetime.now(timezone.utc).isoformat()
        context.append(BaseLLM.apply_delimiter(
            block_name='current_time',
            query=timestamp,
            delimiter_type='caps:'
        ))

        look_back_days = update_period_dict.get(
            self.user_preferences.portfolio_update_frequency, '7'
        )
        for symbol in stock_symobols_to_watch:
            historic_data = self.market.get_historic_value(
                symbol=symbol,
                start=datetime.now(timezone.utc).isoformat(),
                end=(datetime.now(timezone.utc) - timedelta(days=int(look_back_days))).isoformat(),
                aggregation='daily'
            )
            for h in historic_data:
                context.append(historic_data)
        
        # add current portfolio to context
        current_portfolio = self.broker.get_portfolio()
        context.append(current_portfolio)

        return context


    def generate_strategy(self, save_to_db: bool = True) -> StrategyResponse:
        context = self.gather_research_context()
        prompt = self.user_preferences.research_prompt
        period = self.user_preferences.portfolio_update_frequency
        period_string = {
            'hourly': 'hour',
            'daily': 'day',
            'weekly': 'week',
            'monthly': 'month'
        }.get(period, 'week')

        if prompt is None:
            prompt = """
                     You are an absolute gigachad investment banker.
                     You have immaculate picks that generate immediate returns.
                     Your boss has seen you double your portfolio in 1 month many times.
                     This month should be no different.
                     """
        
        llm_request = LLMRequest(
            prompt = prompt,
            background = f"""
                         Perform market research to generate an investment strategy 
                         to be followed by AI agents over a one {period_string} period.
                         Options and crypto are not allowed. 
                         Only buy/sell stocks that are available on public markets.
                         No leverage, only use cash available in the portfolio or 
                         made available through the sale of stocks.
                         """,
            context = context,
            expected_format = StrategyResponse
        )

        strategy = self.research_brain.ask(llm_request)
        if save_to_db:
            self.db.write(
                user=self.user, 
                category='strategy', 
                action={
                    'query': BaseLLM.make_query(llm_request),
                    'response': strategy.model_dump()
                }
            )

        return strategy
    
    def update_portfolio(
        self, strategy: StrategyResponse | None = None, save_to_db: bool = True
    ) -> RelativePortfolio:
        context = self.gather_portfolio_update_context(strategy=strategy)
        prompt = self.user_preferences.portfolio_update_prompt
        if prompt is None:
            prompt = """
                     You are an absolute gigachad investment banker.
                     You have immaculate picks that generate immediate returns.
                     Your boss has seen you double your portfolio in 1 month many times.
                     This month should be no different.
                     """

        llm_request = LLMRequest(
            prompt = prompt,
            background = f"""
                         Given the current investment strategy, 
                         recommend a new portfolio allocation as a RelativePortfolio.
                         Only include stocks that are available on public markets.
                         No leverage, only use cash available in the portfolio or 
                         made available through the sale of stocks.
                         """,
            context = context,
            expected_format = RelativePortfolio
        )

        relative_portfolio = self.portfolio_update_brain.ask(llm_request)
        if save_to_db:
            self.db.write(
                user=self.user, 
                category='portfolio_update', 
                action={
                    'query': BaseLLM.make_query(llm_request),
                    'response': relative_portfolio.model_dump()
                }
            )

        return relative_portfolio


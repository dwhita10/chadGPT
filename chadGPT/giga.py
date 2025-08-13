from pydantic import BaseModel

from chadGPT.data_models import (
    Job, Task, LLMRequest
)
from chadGPT.brain import BaseLLM
from chadGPT.data_models import Preferences
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

    def get_previous_strategy(self) -> str:
        """
        Retrieve the previous strategy from the database.
        This could be implemented to read from a specific table or log.
        """
        actions = self.db.read(user=self.user, category='strategy')
        if actions:
            return actions[-1].action.get('strategy', '')
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

    def generate_strategy(self):
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
        )

        return self.research_brain.ask(llm_request)
    
    


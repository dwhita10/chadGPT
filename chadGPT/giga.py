from chadGPT.data_models import (
    Job, Task, LLMRequest
)
from chadGPT.brain import BaseLLM
from chadGPT.trader import BaseBroker, BaseMarketResearch

# general workflow
# 1. Strategy Generation/Update (frequency)
# 2. Recommend portfolio updates (frequency)
# 3. Implement portfolio update (trades)

class Giga:
    def __init__(
        self, broker: BaseBroker, 
        market: BaseMarketResearch, brain: BaseLLM
    ):
        self.broker = broker
        self.market = market
    
    def generate_strategy(self, brain: BaseLLM, prompt: str | None = None):
        if prompt is None:
            prompt = """
                     You are an absolute gigachad investment banker.
                     You have immaculate picks that generate immediate returns.
                     Your boss has seen you double your portfolio in 1 month many times.
                     This month should be no different.
                     Perform market research to generate an investment strategy 
                     to be followed by AI agents over a one week period.
                     """
        
        llm_request = LLMRequest(
            prompt = prompt,
            background = """
                         Options and crypto are not allowed. 
                         Only buy/sell stocks that are available on public markets.
                         No leverage, only use cash available in the portfolio or 
                         made available through the sale of stocks.
                         """
        )

        return brain.ask(llm_request)
    
    


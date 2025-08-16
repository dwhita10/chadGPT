from abc import ABC, abstractmethod
from typing import Literal
import json
import logging
import os

from openai import OpenAI
from pydantic import BaseModel
import pyperclip

from chadGPT.data_models import LLMRequest, Portfolio
from chadGPT.environment_setup import is_environment_ready


logger = logging.getLogger(__name__)


def apply_delimiter(
    block_name: str, query: str, delimiter_type: Literal['<html>', 'caps:']
) -> str:
    if delimiter_type == '<html>':
        return f"\n<{block_name}>\n{query}\n</{block_name}>\n"
    elif delimiter_type == 'caps:':
        return f"<{block_name.upper()}:\n{query}\n"
    else:
        raise ValueError(f"invalid delimiter_type: {delimiter_type}")


def format_data_model(model: BaseModel | str | list[BaseModel | str]) -> str:
    if isinstance(model, list):
        query = "{\n"
        query += ",\n".join([format_data_model(m) for m in model])
        query += "\n}"
    elif isinstance(model, BaseModel):
        query = (
            f"{model.__class__.__name__}: " +
            f"{model.model_dump_json(indent=None, warnings=False)}"
        )
    elif isinstance(model, str):
        query = model
    else:
        raise TypeError(
            f'Arg model must be type BaseModel or list[BaseModel]; ' +
            f'got {type(model)}'
        )
    
    return query


class BaseLLM(ABC):

    @abstractmethod
    def submit_query(self, query: str) -> str:
        pass
    
    @staticmethod
    def make_query(request: LLMRequest) -> str:
        # unpack the query
        query = ""
        query += apply_delimiter(
            block_name='background',
            query=request.background,
            delimiter_type='<html>'
        )
        if isinstance(request.context,str):
            query += apply_delimiter(
                block_name='context',
                query=request.context,
                delimiter_type='<html>'
            )
        else:
            query += apply_delimiter(
                block_name='context',
                query=format_data_model(request.context),
                delimiter_type='<html>'
            )
        
        query += f"\n<prompt> {request.prompt} </prompt>\n"

        if request.expected_format is not None:

            expected_response = f"Please return an answer matching the below format (given by the pydantic basemodel.model_json_schema() function):\n"
            expected_response += f"{json.dumps(request.expected_format.model_json_schema(), indent=2)}"
            query += apply_delimiter(
                block_name='expected_format',
                query=expected_response,
                delimiter_type='<html>'
            )
        
        return query


    def ask(self, request: LLMRequest) -> str | BaseModel:
        query = self.make_query(request)
        answer = self.submit_query(query)

        if request.expected_format:
            # read answer into dictionary
            logger.debug(f"Received answer: {answer}")
            answer = json.loads(answer)

            # unpack answer into object
            answer = request.expected_format(**answer)
            assert isinstance(answer, request.expected_format)

        return answer


class ConsoleLLM(BaseLLM):
    def submit_query(self, query: str) -> str:
        # print(query)
        pyperclip.copy(query)
        print(
            'Query copied! Paste into your favorite ' \
            'LLM tool and copy the output before ' \
            'continuing (or paste output below)'
        )
        output = input('output:')
        if len(output.strip()) == 0:
            # check the pyperclip paste output
            output = pyperclip.paste()
        
        if len(output.strip()) == 0:
            print('No output received! Try again.')
            return self.submit_query(query)
        
        return output

class OpenAILLM(BaseLLM):
    def __init__(self, web_search: bool = False, model_name: str = "gpt-4.1-mini"):
        self.web_search = web_search
        self.api_key = self.get_api_key()
        self.model_name = model_name
        self.client = OpenAI(
            api_key=self.api_key
        )

    @staticmethod
    def get_api_key() -> str:
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key is None:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        return api_key
    
    def ask(self, request: LLMRequest) -> str | BaseModel:
        expected_format = request.expected_format
        request.expected_format = None  # remove expected format for the query
        query = self.make_query(request)
        answer = self.submit_query(query, expected_format)

        if request.expected_format:
            # read answer into dictionary
            logger.debug(f"Received answer: {answer}")
            answer = json.loads(answer)

            # unpack answer into object
            answer = request.expected_format(**answer)
            assert isinstance(answer, request.expected_format)

        return answer

    def submit_query(self, query: str, expected_format: BaseModel | None = None) -> str:
        
        kwargs = {'input': query, 'model': self.model_name}
        if self.web_search:
            kwargs['tools'] = [{"type": "web_search_preview"}]
            kwargs['tool_choice'] = {"type": "web_search_preview"}
        
        if expected_format:
            kwargs['text_format'] = expected_format
            function_name = self.client.responses.parse
            output_name = 'output_parsed'
        else:
            function_name = self.client.responses.create
            output_name = 'output_text'
        
        logger.debug(f"OpenAI request: {kwargs}")


        response = function_name(**kwargs)

        logger.debug(f"OpenAI response: {response}")
        logger.debug(f"Saved answer: {response.output_text}")
        answer = getattr(response, output_name, '')
        return answer

if __name__ == "__main__":
    # test the consoleLLM
    # llm = ConsoleLLM()
    # request = LLMRequest(
    #     prompt='Pretty Please', 
    #     background='Testing your ability to make a complex json',
    #     context='this is a test, please insert plausible numbers as needed', 
    #     expected_format=Portfolio
    # )
    # answer = llm.ask(request)
    # assert isinstance(answer, request.expected_format)
    # print(type(answer))
    # print(answer.model_dump_json(indent=2, exclude_none=True))

    # test the OpenAILLM
    llm = OpenAILLM(web_search=False, model_name="gpt-4.1")
    request = LLMRequest(
        prompt='Pretty Please', 
        background='Testing your ability to make a complex json',
        context='this is a test, please insert plausible numbers as needed', 
        expected_format=Portfolio
    )
    answer = llm.ask(request)
    print(answer)
    print(type(answer))
    assert isinstance(answer, request.expected_format)
    

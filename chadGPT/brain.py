from abc import ABC, abstractmethod
from typing import Literal
import json

from pydantic import BaseModel
import pyperclip

from chadGPT.data_models import LLMRequest, Portfolio


class BaseLLM(ABC):

    @abstractmethod
    def submit_query(self, query: str) -> str:
        pass
    
    @staticmethod
    def apply_delimiter(
        block_name: str, query: str, delimiter_type: Literal['<html>', 'caps:']
    ) -> str:
        if delimiter_type == '<html>':
            return f"\n<{block_name}>\n{query}\n</{block_name}>\n"
        elif delimiter_type == 'caps:':
            return f"<{block_name.upper()}:\n{query}\n"
        else:
            raise ValueError(f"invalid delimiter_type: {delimiter_type}")

    def format_data_model(self, model: BaseModel | str | list[BaseModel | str]) -> str:
        if isinstance(model, list):
            query = "{\n"
            query += ",\n".join([self.format_data_model(m) for m in model])
            query += "\n}"
        elif isinstance(model, BaseModel):
            query = (
                f"{model.__name__}: " +
                f"{model.model_dump_json(indent=None, warnings=False)}"
            )
        elif isinstance(model, str):
            query = model
        else:
            raise TypeError(
                f'Arg model must be type BaseModel or list[BaseModel]; ' +
                f'got {type(model)}'
            )

    def ask(self, request: LLMRequest) -> str | BaseModel:
        # unpack the query
        query = ""
        query += self.apply_delimiter(
            block_name='background',
            query=request.background,
            delimiter_type='<html>'
        )
        if isinstance(request.context,str):
            query += self.apply_delimiter(
                block_name='context',
                query=request.context,
                delimiter_type='<html>'
            )
        else:
            query += self.apply_delimiter(
                block_name='context',
                query=self.format_data_model(request.context),
                delimiter_type='<html>'
            )
        
        query += f"\n<prompt> {request.prompt} </prompt>\n"

        if request.expected_format is not None:

            query += f"Please return an answer matching the below format (given by the pydantic basemodel.model_json_schema() function):\n"
            query += f"{json.dumps(request.expected_format.model_json_schema(), indent=2)}"
        
        answer = self.submit_query(query)

        if request.expected_format:
            # read answer into dictionary
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


if __name__ == "__main__":
    # test the consoleLLM
    llm = ConsoleLLM()
    request = LLMRequest(
        prompt='Pretty Please', 
        background='Testing your ability to make a complex json',
        context='this is a test, please insert plausible numbers as needed', 
        expected_format=Portfolio
    )
    answer = llm.ask(request)
    assert isinstance(answer, request.expected_format)
    print(type(answer))

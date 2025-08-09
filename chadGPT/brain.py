from abc import ABC, abstractmethod
import json

from chadGPT.data_models import LLMRequest


class BaseLLM(ABC):

    @abstractmethod
    def submit_query(self, query: str):
        pass

    def ask(self, request: LLMRequest):
        # unpack the query
        query = ""
        query += f"\n<background> {request.background} </background>\n"
        if isinstance(request.context,str):
            query += f"\n<context>\n {request.context} \n</context>\n"
        else:
            query += f"\n<context>\n"
            for c in request.context:
                query += f"{c.__name__}: {
                    c.model_dump_json(
                        indent=None, warnings=False
                    )
                    }"
            query += f"\n</context>"
        
        query += f"\n<prompt> {request.prompt} </prompt>\n"

        if request.expected_format is not None:

            query += f"Please return an answer matching the below format (given by the pydantic basemodel.model_json_schema() function):\n"
            query += f"{json.dumps(request.expected_format.model_json_schema(), indent=2)}"
        
        return self.submit_query(query)


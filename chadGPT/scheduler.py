from abc import ABC, abstractmethod
from typing import Any

from chadGPT.data_models import Task, Job

class Scheduler(ABC):
    def __init__(self, job: Job):
        self.job = job
    
    @abstractmethod
    def schedule(self):
        # schedule the "run" function of this object based on the self.job.schedule
        pass
    
    @staticmethod
    def run_task(task: Task, previous_task_output: tuple[Any] | None = None):
        task_args = task.args or ()
        if previous_task_output is not None:
            all_args = (*task_args, *previous_task_output)
        else:
            all_args = (*task_args,)

        output = task.func(*all_args)

        return output

    def run(self):
        output = None
        for task in self.job.tasks:
            output = self.run_task(task, output)
        
        return output


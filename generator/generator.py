from abc import ABC, abstractclassmethod, abstractstaticmethod, abstractmethod


class Generator(ABC):

    @abstractmethod
    def __init__(self, data_source: str, generator_id: int,
                 priority: int, task_pipeline: list) -> None:
        self.data_source = data_source
        self.generator_id = generator_id
        self.priority = priority
        self.task_pipeline = task_pipeline
        self.task_pipeline.append({'service_name': 'end', 'execute_address': '', 'execute_data': {}})

    '''Should be implemented as a while loop that yields tasks'''

    @abstractmethod
    def run(self):
        pass

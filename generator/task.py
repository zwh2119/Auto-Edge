from abc import ABC, abstractmethod, abstractclassmethod, abstractstaticmethod, abstractproperty


class Task(ABC):
    @abstractclassmethod
    def task_type(cls) -> str:
        pass

    @abstractclassmethod
    def task_description(cls) -> str:
        pass

    @abstractmethod
    def __init__(self, data: object, seq_id: int, source_id: int,
                 priority: int, metadata: dict, task_dag: list) -> None:
        self.data = data
        self.seq_id = seq_id
        self.source_id = source_id
        self.priority = priority
        self.metadata = metadata
        self.task_dag = task_dag
        self.execute_data = {}

    @abstractmethod
    def serialize(self) -> dict:
        pass

    @abstractstaticmethod
    def deserialize(data: dict):
        pass

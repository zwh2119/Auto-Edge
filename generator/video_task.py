from generator.task import Task


class VideoTask(Task):
    def __init__(self, data: object, seq_id: int, source_id: int,
                 priority: int, metadata: dict, task_dag: list):
        super().__init__(data, seq_id, source_id, priority, metadata, task_dag)

    @classmethod
    def task_type(cls) -> str:
        return 'video'

    @classmethod
    def task_description(cls) -> str:
        return 'Video task'

    def serialize(self) -> dict:
        return {'data': self.data, 'seq_id': self.seq_id, 'source_id': self.source_id,
                'priority': self.priority, 'metadata': self.metadata, 'task_dag': self.task_dag,
                'execute_data': self.execute_data}

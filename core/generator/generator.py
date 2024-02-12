from core.lib.content import Task


class Generator:
    def __init__(self, source_id: int, task_pipeline: list):
        self.source_id = source_id
        self.task_pipeline = Task.extract_pipeline(task_pipeline)

    def run(self):
        assert None, 'Base Generator should not be invoked directly!'

from task import Task


class VideoTask(Task):
    def __init__(self):
        super().__init__()

    @staticmethod
    def serialize(task):
        pass

    @staticmethod
    def deserialize(data: dict):
        pass

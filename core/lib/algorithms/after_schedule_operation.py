import abc
from lib.common import ClassFactory, ClassType
from lib.content import Task

__all__ = ('SimpleOperation',)


class BaseOperation(metaclass=abc.ABCMeta):
    def __call__(self, system, scheduler_policy):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_ASO, alias='simple')
class SimpleOperation(BaseOperation, abc.ABC):
    def __init__(self):
        self.default_metadata = {
            'resolution': '1080p',
            'fps': 30,
            'encoding': 'mp4v',
            'batch_size': 8
        }

    def __call__(self, system, scheduler_policy):
        if scheduler_policy is None:
            system.meta_data.update(self.default_metadata)
            default_execute_device = system.local_device
            system.task_pipeline = Task.set_execute_device(system.task_pipeline, default_execute_device)
        else:
            pipeline = scheduler_policy['pipeline']
            system.task_pipeline = Task.extract_pipeline_from_dict(pipeline)
            del scheduler_policy['pipeline']
            system.meta_data.update(scheduler_policy)

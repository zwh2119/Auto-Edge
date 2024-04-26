import abc
from lib.common import ClassFactory, ClassType
from lib.content import Task

__all__ = ('SimpleOperation',)


class BaseOperation(metaclass=abc.ABCMeta):
    def __call__(self, system):
        raise NotImplementedError


@ClassFactory.register(ClassType.GEN_BSO, alias='simple')
class SimpleOperation(BaseOperation, abc.ABC):
    def __init__(self):
        pass

    def __call__(self, system):
        parameters = {'source_id': system.source_id,
                      'meta_data': system.raw_meta_data,
                      'pipeline': Task.extract_dict_from_pipeline(system.task_pipelin)}

        return parameters

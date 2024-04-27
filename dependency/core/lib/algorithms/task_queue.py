import abc
import threading
from queue import Queue

from core.lib.common import ClassFactory, ClassType
from core.lib.content import Task

__all__ = ('SimpleQueue',)


class BaseQueue(metaclass=abc.ABCMeta):
    def get(self):
        raise NotImplementedError

    def size(self):
        raise NotImplementedError

    def put(self, task):
        raise NotImplementedError

    def empty(self):
        raise NotImplementedError


@ClassFactory.register(ClassType.PRO_QUEUE, alias='simple')
class SimpleQueue(BaseQueue, abc.ABC):
    def __init__(self):
        self._queue = Queue()
        self.lock = threading.Lock()

    def get(self):
        with self.lock:
            if self._queue.empty():
                return None
            return self._queue.get()

    def put(self, task: Task) -> None:
        with self.lock:
            self._queue.put(task)

    def size(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

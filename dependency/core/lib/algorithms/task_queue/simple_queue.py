import abc
import threading
from queue import Queue

from core.lib.common import ClassFactory, ClassType
from core.lib.content import Task
from .base_queue import BaseQueue

__all__ = ('SimpleQueue',)


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

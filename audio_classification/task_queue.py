import threading
from queue import PriorityQueue as PQ
from task import Task


class LocalPriorityQueue:
    def __init__(self, max_size=10) -> None:
        self._queue = PQ()
        self.lock = threading.Lock()

        self._MAX_SIZE = 10

    def put(self, task: Task) -> None:
        with self.lock:
            if self._queue.qsize() > self._MAX_SIZE:
                for _ in range(self._MAX_SIZE//2):
                    self._queue.get()
            self._queue.put(task)

    def get(self):
        with self.lock:
            if self._queue.empty():
                return None
            return self._queue.get()

    def size(self) -> int:
        with self.lock:
            return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

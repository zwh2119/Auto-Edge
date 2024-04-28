import abc


class BaseQueue(metaclass=abc.ABCMeta):
    def get(self):
        raise NotImplementedError

    def size(self):
        raise NotImplementedError

    def put(self, task):
        raise NotImplementedError

    def empty(self):
        raise NotImplementedError

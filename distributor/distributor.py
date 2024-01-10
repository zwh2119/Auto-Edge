from abc import ABC, abstractclassmethod, abstractstaticmethod, abstractmethod


class Distributor(ABC):
    @abstractclassmethod
    def distributor_type(cls) -> str:
        pass

    @abstractclassmethod
    def distributor_description(cls) -> str:
        pass

    @abstractmethod
    def __init__(self, distributor_id: str) -> None:
        self.distributor_id = distributor_id

    '''Should be implemented as a while loop that yields tasks'''

    @abstractmethod
    def run(self):
        pass

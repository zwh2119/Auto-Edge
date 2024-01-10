from distributor import Distributor


class VideoDistributor(Distributor):
    def __init__(self, distributor_id: str) -> None:
        super().__init__(distributor_id)

        self.local_task_queue = []

    @classmethod
    def distributor_type(cls) -> str:
        return 'video'

    @classmethod
    def distributor_description(cls) -> str:
        return 'Video distributor'

    def run(self):
        pass

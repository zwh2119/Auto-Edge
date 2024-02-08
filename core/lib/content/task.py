from service import Service


class Task:
    def __init__(self,
                 source_id: int,
                 task_id: int,
                 pipeline: list,
                 metadata: dict = None,
                 content: object = None):

        self.__source_id = source_id
        self.__task_id = task_id

        self.__metadata = metadata

        self.__pipeline_flow = Task.__extract_pipeline(pipeline)

        self.__cur_flow_index = 0

        self.__content_data = content

        self.__scenario_data = {}

        self.__tmp_data = {}

    @staticmethod
    def __extract_pipeline(pipeline):
        return {}

    def get_source_id(self):
        return self.__source_id

    def get_task_id(self):
        return self.__task_id

    def get_pipeline(self):
        pass

    def get_current_stage(self):
        pass

    def flow_index(self):
        return self.__cur_flow_index

    def step_to_next_stage(self):
        self.__cur_flow_index += 1

        assert 0 <= self.__cur_flow_index < len(self.__pipeline_flow), \
            f'Illegal flow index of "{self.__cur_flow_index}"!'

    @staticmethod
    def serialize(task):
        return {'source_id': task.__source_id, 'task_id': task.__task_id}

    @staticmethod
    def deserialize(data: dict):
        return Task(data['source_id'], data['task_id'])

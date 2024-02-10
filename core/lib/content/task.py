from service import Service


class Task:
    def __init__(self,
                 source_id: int,
                 task_id: int,
                 pipeline: list = None,
                 metadata: dict = None,
                 content: object = None,
                 scenario: dict = None,
                 temp: dict = None):
        self.__source_id = source_id
        self.__task_id = task_id

        self.__metadata = metadata

        self.__pipeline_flow = Task.__extract_pipeline(pipeline) if pipeline else None

        self.__cur_flow_index = 0

        self.__content_data = content

        self.__scenario_data = scenario if scenario else {}

        self.__tmp_data = temp if temp else {}

    @staticmethod
    def __extract_pipeline(pipeline: list):
        pipeline_flow = []
        for in_service in pipeline:
            assert 'service_name' in in_service, 'invalid service without "service_name"!'
            service = Service(in_service['service_name'])
            pipeline_flow.append(service)

        pipeline_flow.append(Service('end'))

        return pipeline_flow

    def get_source_id(self):
        return self.__source_id

    def get_task_id(self):
        return self.__task_id

    def get_pipeline(self):
        return self.__pipeline_flow

    def set_pipeline(self, pipeline):
        self.__pipeline_flow = pipeline

    def get_content(self):
        return self.__content_data

    def set_content(self, content):
        self.__content_data = content

    def get_scenario_data(self):
        return self.__scenario_data

    def set_scenario_data(self, data: dict):
        self.__scenario_data = data

    def add_scenario(self, data: dict):
        self.__scenario_data.update(data)

    def get_tmp_data(self):
        return self.__tmp_data

    def set_tmp_data(self, data: dict):
        self.__tmp_data = data

    def get_current_service(self):
        service = self.__pipeline_flow[self.__cur_flow_index]
        return service.get_service_name(), service.get_execute_device()

    def save_transmit_time(self, transmit_time):
        self.__pipeline_flow[self.__cur_flow_index].set_transmit_time(transmit_time=transmit_time)

    def save_execute_time(self, execute_time):
        self.__pipeline_flow[self.__cur_flow_index].set_execute_time(execute_time=execute_time)

    def calculate_total_time(self):
        assert self.__pipeline_flow, 'pipeline of task is empty!'
        assert self.__cur_flow_index < len(self.__pipeline_flow), 'pipeline is not completed!'
        total_time = 0
        for service in self.__pipeline_flow:
            total_time += service.get_service_total_time()

        return total_time

    def get_flow_index(self):
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

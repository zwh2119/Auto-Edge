from .service import Service


class Task:
    def __init__(self,
                 source_id: int,
                 task_id: int,
                 pipeline: list = None,
                 flow_index: int = 0,
                 metadata: dict = None,
                 raw_metadata: dict = None,
                 content: object = None,
                 scenario: dict = None,
                 temp: dict = None,
                 file_path: str = None):
        self.__source_id = source_id
        self.__task_id = task_id

        self.__metadata = metadata

        self.__raw_metadata = raw_metadata

        self.__pipeline_flow = pipeline

        self.__cur_flow_index = flow_index

        self.__content_data = content

        self.__scenario_data = scenario if scenario else {}

        self.__tmp_data = temp if temp else {}

        self.__file_path = file_path

    @staticmethod
    def extract_pipeline_from_dict(pipeline: list):
        pipeline_flow = []
        for in_service in pipeline:
            assert 'service_name' in in_service, 'invalid service without "service_name"!'
            service = Service(in_service['service_name'])
            if 'execute_device' in in_service:
                service.set_execute_device(in_service['execute_device'])
            pipeline_flow.append(service)

        pipeline_flow.append(Service('end'))

        return pipeline_flow

    @staticmethod
    def extract_dict_from_pipeline(pipeline_flow: list):
        pipeline_list = []
        for service in pipeline_flow:
            if service.get_service_name() == 'end':
                continue
            pipeline = {'service_name': service.get_service_name(),
                        'execute_device': service.get_execute_device()}
            pipeline_list.append(pipeline)

        return pipeline_list

    def get_source_id(self):
        return self.__source_id

    def get_task_id(self):
        return self.__task_id

    def get_pipeline(self):
        return self.__pipeline_flow

    def set_pipeline(self, pipeline):
        self.__pipeline_flow = pipeline

    def set_initial_pipeline(self, pipeline):
        self.__pipeline_flow = Task.extract_pipeline_from_dict(pipeline)

    def get_metadata(self):
        return self.__metadata

    def set_metadata(self, data: dict):
        self.__metadata = data

    def get_raw_metadata(self):
        return self.__raw_metadata

    def set_raw_metadata(self, data: dict):
        self.__raw_metadata = data

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

    def get_file_path(self):
        return self.__file_path

    def set_file_path(self, path: str):
        self.__file_path = path

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

    def set_initial_execute_device(self, hostname):
        assert self.__pipeline_flow, 'pipeline is empty!'
        for service in self.__pipeline_flow:
            service.set_execute_device(hostname)

    @staticmethod
    def set_execute_device(pipeline, hostname):
        assert pipeline, 'pipeline is empty!'
        for service in pipeline:
            service.set_execute_device(hostname)

    @staticmethod
    def serialize(task: 'Task'):
        pipeline_serialize = []
        pipeline = task.get_pipeline()
        for service in pipeline:
            pipeline_serialize.append(Service.serialize(service))
        return {
            'source_id': task.get_source_id(),
            'task_id': task.get_task_id(),
            'pipeline': pipeline_serialize,
            'cur_flow_index': task.get_flow_index(),
            'meta_data': task.get_metadata(),
            'raw_meta_data': task.get_raw_metadata(),
            'content_data': task.get_content(),
            'scenario_data': task.get_scenario_data(),
            'tmp_data': task.get_tmp_data(),
            'file_path': task.get_file_path()
        }

    @staticmethod
    def deserialize(data: dict):
        pipeline = []
        for s in data['pipeline']:
            service = Service.deserialize(s)
            pipeline.append(service)
        return Task(data['source_id'],
                    data['task_id'],
                    pipeline=pipeline,
                    flow_index=data['cur_flow_index'],
                    metadata=data['meta_data'],
                    raw_metadata=data['raw_meta_data'],
                    content=data['content_data'],
                    scenario=data['scenario_data'],
                    temp=data['tmp_data'],
                    file_path=data['file_path']
                    )

class Service:
    def __init__(self, service_name, execute_device='',
                 transmit_time=0, execute_time=0):
        self.__service_name = service_name
        self.__execute_device = execute_device
        self.__transmit_time = transmit_time
        self.__execute_time = execute_time

    def get_service_name(self):
        return self.__service_name

    def set_service_name(self, service_name):
        self.__service_name = service_name

    def get_execute_device(self):
        return self.__execute_device

    def set_execute_device(self, execute_device):
        self.__execute_device = execute_device

    def set_transmit_time(self, transmit_time):
        assert transmit_time >= 0, f'transmit time of service "{self.__service_name}" is negative: {transmit_time}!'
        self.__transmit_time = transmit_time

    def set_execute_time(self, execute_time):
        assert execute_time >= 0, f'execute time of service "{self.__service_name}" is negative: {execute_time}!'
        self.__execute_time = execute_time

    def get_transmit_time(self):
        return self.__transmit_time

    def get_execute_time(self):
        return self.__execute_time

    def get_service_total_time(self):
        return self.__execute_time + self.__execute_time

    @staticmethod
    def serialize(service: 'Service'):
        return {
            'service_name': service.get_service_name(),
            'execute_device': service.get_execute_device(),
            'execute_data': {'transmit_time': service.get_transmit_time(),
                             'execute_time': service.get_execute_time()}
        }

    @staticmethod
    def deserialize(data):
        service = Service(data['service_name'], data['execute_device'],
                          execute_time=data['execute_data']['execute_time'],
                          transmit_time=data['execute_data']['transmit_time'])
        return service

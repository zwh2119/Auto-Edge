class NetworkAPIPath:
    CONTROLLER_TASK = '/submit_task'
    CONTROLLER_RETURN = '/process_return'
    PROCESSOR_PROCESS = '/predict'
    DISTRIBUTOR_DISTRIBUTE = '/distribute'
    DISTRIBUTOR_RESULT = '/result'
    DISTRIBUTOR_FILE = '/file'
    SCHEDULER_SCHEDULE = '/schedule'
    SCHEDULER_SCENARIO = '/scenario'
    SCHEDULER_RESOURCE = '/resource'


class NetworkAPIMethod:
    CONTROLLER_TASK = 'POST'
    CONTROLLER_RETURN = 'POST'
    PROCESSOR_PROCESS = 'POST'
    DISTRIBUTOR_DISTRIBUTE = 'POST'
    DISTRIBUTOR_RESULT = 'GET'
    DISTRIBUTOR_FILE = 'GET'
    SCHEDULER_SCHEDULE = 'GET'
    SCHEDULER_SCENARIO = 'POST'
    SCHEDULER_RESOURCE = 'POST'



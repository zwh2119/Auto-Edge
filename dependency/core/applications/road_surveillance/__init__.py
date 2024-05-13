def get_current_service_name():
    from core.lib.common import Context
    service_name = Context.get_parameter('service_name')
    del Context

    return service_name


if get_current_service_name() == 'car_detection':
    from . import car_detection

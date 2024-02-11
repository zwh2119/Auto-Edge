import time


class TimeEstimator:

    @staticmethod
    def record_pipeline_ts(data: dict, flow_index: int, transmit: bool = True) -> (bool, dict, float):
        """
        record pipeline timestamp in system
        :param data: time dictionary
        :param flow_index: index in pipeline flow
        :param transmit: is transmit time record (transmit time or service time)
        :return: is_end: is the end of time estimation
                 data: time dictionary
                 duration: time estimation result

        """
        return TimeEstimator.record_ts(data, f'transmit_time_{flow_index}' if transmit else f'service_time_{flow_index}')

    @staticmethod
    def record_ts(data: dict, tag: str) -> (bool, dict, float):
        """
        record timestamp in system
        :param data: time dictionary
        :param tag: name of time ticket
        :return: is_end: is the end of time estimation
                 data: time dictionary
                 duration: time estimation result

        """

        if tag in data:
            start_time = data[tag]
            end_time = time.time()
            del data[tag]
            is_end = True
            duration = end_time - start_time
        else:
            data[tag] = time.time()
            is_end = False
            duration = 0

        return is_end, data, duration

    @staticmethod
    def estimate_duration_time(func):
        def wrapper(*args, **kw):
            start = time.time()
            func(*args, **kw)
            end = time.time()

            return end-start

        return wrapper

    @staticmethod
    def estimate_duration_time_print(func):
        def wrapper(*args, **kw):
            start = time.time()
            func(*args, **kw)
            end = time.time()

            print('function {} cost time {:.2f}s'.format(func.__name__, end-start))

        return wrapper


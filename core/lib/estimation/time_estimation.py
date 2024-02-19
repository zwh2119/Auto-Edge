import time


class TimeEstimator:

    @staticmethod
    def record_pipeline_ts(data: dict, flow_index: int, is_end: bool, transmit: bool = True) -> (bool, dict, float):
        """
        record pipeline timestamp in system
        :param data: time dictionary
        :param flow_index: index in pipeline flow
        :param is_end: if recording the end of current timestamp
        :param transmit: is transmit time record (transmit time or service time)
        :return: is_end: is the end of time estimation
                 data: time dictionary
                 duration: time estimation result

        """
        return TimeEstimator.record_ts(data,
                                       f'transmit_time_{flow_index}' if transmit else f'service_time_{flow_index}',
                                       is_end=is_end)

    @staticmethod
    def record_ts(data: dict, tag: str, is_end: bool = False) -> (dict, float):
        """
        record timestamp in system
        :param data: time dictionary
        :param tag: name of time ticket
        :param is_end: if recording the end of current timestamp
        :return: data: time dictionary
                 duration: time estimation result

        """

        if is_end:
            assert tag in data, f'record end timestamp of {tag}, but start timestamp does not exists!'
            start_time = data[tag]
            end_time = time.time()
            del data[tag]
            duration = end_time - start_time
        else:
            assert tag not in data, f'record start timestamp of {tag}, but start timestamp has existed in system!'
            data[tag] = time.time()
            duration = 0

        return data, duration

    @staticmethod
    def estimate_duration_time(func):
        def wrapper(*args, **kw):
            start = time.time()
            func(*args, **kw)
            end = time.time()

            return end - start

        return wrapper

    @staticmethod
    def estimate_duration_time_print(func):
        def wrapper(*args, **kw):
            start = time.time()
            func(*args, **kw)
            end = time.time()

            print('function {} cost time {:.2f}s'.format(func.__name__, end - start))

        return wrapper

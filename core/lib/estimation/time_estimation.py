import time


class TimeEstimator:

    @staticmethod
    def record_pipeline_time(data: dict, flow_index: int, transmit: bool = True) -> (bool, dict, float):
        """
        record time in system
        :param data: time dictionary
        :param flow_index: index in pipeline flow
        :param transmit: is transmit time record (transmit time or service time)
        :return: is_end: is the end of time estimation
                 data: time dictionary
                 duration: time estimation result

        """
        return TimeEstimator.record_time(data, f'transmit_time_{flow_index}' if transmit else f'service_time_{flow_index}')

    @staticmethod
    def record_time(data: dict, tag: str) -> (bool, dict, float):
        """
        record time in system
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

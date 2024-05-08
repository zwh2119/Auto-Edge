import time
from core.lib.content import Task
from core.lib.common import LOGGER


class Timer:
    def __init__(self, label=""):
        self.label = label

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        if self.label:
            LOGGER.info(f"[{self.label}] Execution time: {self.elapsed_time:.4f}s")
        else:
            LOGGER.info(f"Execution time: {self.elapsed_time:.4f}s")

    def get_elapsed_time(self):
        return self.elapsed_time


class TimeEstimator:

    @staticmethod
    def record_pipeline_ts(task: Task, is_end: bool, sub_tag: str = 'transmit') -> (Task, float):
        """
        record pipeline timestamp in system
        :param task: pipeline task
        :param is_end: if recording the end of current timestamp
        :param sub_tag: sub tag of ts record name (eg:transmit_time_1)
        :return: task: pipeline task with recorded time
                 duration: time estimation result

        """
        data, duration = TimeEstimator.record_ts(task.get_tmp_data(),
                                                 f'{sub_tag}_time_{task.get_flow_index()}',
                                                 is_end=is_end)
        task.set_tmp_data(data)
        return task, duration

    @staticmethod
    def record_task_ts(task: Task, tag: str, is_end: bool = False) -> (Task, float):
        """

        :param task: pipeline task
        :param tag: name of time ticket
        :param is_end: if recording the end of current timestamp
        :return: task: pipeline task with recorded time
                 duration: time estimation result
        """

        data, duration = TimeEstimator.record_ts(task.get_tmp_data(),
                                                 tag=tag,
                                                 is_end=is_end)
        task.set_tmp_data(data)
        return task, duration

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

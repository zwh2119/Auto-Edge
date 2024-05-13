import time

from core.lib.estimation import TimeEstimator


@TimeEstimator.estimate_duration_time
def func():
    time.sleep(3)


@TimeEstimator.estimate_duration_time_print
def func2():
    time.sleep(3)


if __name__ == '__main__':
    func2()

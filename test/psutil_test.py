import time

import psutil


def psutil_test():
    print('################')
    print('cpu: ', psutil.cpu_percent())
    per_cpu = psutil.cpu_percent(percpu=True)
    print('per cpu:', per_cpu)
    print('avg cpu:', sum(per_cpu)/len(per_cpu))
    print('mem: ', psutil.virtual_memory().percent)
    print()


if __name__ == '__main__':
    while True:
        psutil_test()
        time.sleep(1)

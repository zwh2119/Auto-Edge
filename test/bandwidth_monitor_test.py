import threading
import time

import psutil
import iperf3
import tcping

destination_ip= '114.212.81.11'
destination_port = 5201

def total_bandwidth_test():
    while True:
        start_upload = psutil.net_io_counters().bytes_sent * 8 / 1024 / 1024
        time.sleep(1)
        end_upload = psutil.net_io_counters().bytes_sent * 8 / 1024 / 1024
        print(end_upload - start_upload)


def iperf3_client():
    p = tcping.Ping(destination_ip, destination_port)
    # try:
    #     p.ping(1)
    # except Exception as e:
    #     pass
    if p._failed != 0:
        print('connection failed!')
        return

    client = iperf3.Client()
    client.duration = 1
    client.server_hostname = destination_ip
    client.port = destination_port
    client.protocol = 'tcp'

    print('Connecting to {0}:{1}'.format(client.server_hostname, client.port))
    result = client.run()

    if result.error:
        print(result.error)
    else:
        print('')
        print('Test completed:')
        print('  started at         {0}'.format(result.time))
        print('  bytes transmitted  {0}'.format(result.sent_bytes))
        print('  retransmits        {0}'.format(result.retransmits))
        print('  avg cpu load       {0}%\n'.format(result.local_cpu_total))

        print('Average transmitted data in all sorts of networky formats:')
        print('  bits per second      (bps)   {0}'.format(result.sent_bps))
        print('  Kilobits per second  (kbps)  {0}'.format(result.sent_kbps))
        print('  Megabits per second  (Mbps)  {0}'.format(result.sent_Mbps))
        print('  KiloBytes per second (kB/s)  {0}'.format(result.sent_kB_s))
        print('  MegaBytes per second (MB/s)  {0}'.format(result.sent_MB_s))

def print_test():
    while True:
        print('...')
        time.sleep(0.1)

if __name__ == '__main__':
    # threading.Thread(target=print_test).start()
    # while True:
    #     iperf3_client()
    #     time.sleep(2)

    total_bandwidth_test()
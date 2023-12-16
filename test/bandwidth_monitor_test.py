import time

import psutil
import iperf3


def total_bandwidth_test():
    start_upload = psutil.net_io_counters().bytes_sent * 8 / 1024 / 1024
    time.sleep(1)
    end_upload = psutil.net_io_counters().bytes_sent * 8 / 1024 / 1024
    print(end_upload - start_upload)


def iperf3_client():
    client = iperf3.Client()
    client.duration = 1
    client.server_hostname = '114.212.81.11'
    client.port = 5201

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


if __name__ == '__main__':
    iperf3_client()

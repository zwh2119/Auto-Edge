import threading

import iperf3


def iperf_server(port):
    server = iperf3.Server()
    server.port = port
    print('Running server: {0}:{1}'.format(server.bind_address, server.port))

    while True:
        try:
            result = server.run()
        except Exception as e:
            continue

        if result.error:
            print(result.error)
        else:
            print('')
            print('Test results from {0}:{1}'.format(result.remote_host,
                                                     result.remote_port))
            print('  started at         {0}'.format(result.time))
            print('  bytes received     {0}'.format(result.received_bytes))

            print('Average transmitted received in all sorts of networky formats:')
            print('  bits per second      (bps)   {0}'.format(result.received_bps))
            print('  Kilobits per second  (kbps)  {0}'.format(result.received_kbps))
            print('  Megabits per second  (Mbps)  {0}'.format(result.received_Mbps))
            print('  KiloBytes per second (kB/s)  {0}'.format(result.received_kB_s))
            print('  MegaBytes per second (MB/s)  {0}'.format(result.received_MB_s))
            print('')


if __name__ == '__main__':
    ports = [5201, 5202]
    for single_port in ports:
        threading.Thread(target=iperf_server, args=(single_port,)).start()

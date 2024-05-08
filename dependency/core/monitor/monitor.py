import json
import time

import iperf3
import psutil
import threading

from core.lib.common import LOGGER, Context, timeout
from core.lib.network import NodeInfo, get_merge_address, NetworkAPIPath, NetworkAPIMethod, http_request


class Monitor:
    def __init__(self):
        self.cpu = 0
        self.memory = 0
        self.bandwidth = 0

        self.monitor_interval = Context.get_parameter('interval', direct=False)

        self.scheduler_ip = NodeInfo.hostname2ip(Context.get_parameter('scheduler_name'))
        self.scheduler_port = Context.get_parameter('scheduler_port')
        self.scheduler_address = get_merge_address(self.scheduler_ip,
                                                   port=self.scheduler_port,
                                                   path=NetworkAPIPath.SCHEDULER_RESOURCE)

        self.local_device = NodeInfo.get_local_device()
        self.is_iperf3_server = Context.get_parameter('iperf3_server', direct=False)
        self.iperf3_server_ip = NodeInfo.hostname2ip(Context.get_parameter('iperf3_server_name'))
        if self.is_iperf3_server:
            self.iperf3_ports = Context.get_parameter('iperf3_ports', direct=False)
            self.run_iperf_server()
        else:
            self.iperf3_port = Context.get_parameter('iperf3_port')

        self.initialize_monitor()

    def initialize_monitor(self):
        self.cpu = 0
        self.memory = 0
        self.bandwidth = 0

    def monitor_cpu(self):
        self.cpu = self.get_cpu()

    def monitor_memory(self):
        self.memory = self.get_memory()

    def monitor_bandwidth(self):
        self.bandwidth = self.get_bandwidth(self.iperf3_server_ip, self.iperf3_port)

    @staticmethod
    def get_cpu():
        return psutil.cpu_percent()

    @staticmethod
    def get_memory():
        return psutil.virtual_memory().percent

    @staticmethod
    def get_bandwidth(server_ip, server_port):
        @timeout(2)
        def fetch_bandwidth_by_iperf3(iperf3_client):
            result = iperf3_client.run()
            return result

        client = iperf3.Client()
        client.duration = 1
        client.server_hostname = server_ip
        client.port = server_port
        client.protocol = 'tcp'

        try:

            result_info = fetch_bandwidth_by_iperf3(client)

            if result_info.error:
                LOGGER.warning(f'resource monitor iperf3 error: {result_info.error}')

            bandwidth_result = result_info.sent_Mbps

        except Exception as e:
            LOGGER.exception(f'[Iperf3 Timeout] {e}')
            bandwidth_result = 0

        return bandwidth_result

    def run_iperf_server(self):
        for port in self.iperf3_ports:
            threading.Thread(target=self.iperf_server, args=(port,)).start()

    @staticmethod
    def iperf_server(port):
        server = iperf3.Server()
        server.port = port
        LOGGER.debug(f'[Iperf3 Server] Running iperf3 server: {server.bind_address}:{server.port}')

        while True:
            try:
                result = server.run()
            except Exception as e:
                LOGGER.exception(e)
                continue

            if result.error:
                LOGGER.warning(result.error)

    def monitor_resource(self):
        threads = [
            threading.Thread(target=self.monitor_cpu),
            threading.Thread(target=self.monitor_memory),

        ]
        if not self.is_iperf3_server:
            threads.extend(
                [threading.Thread(target=self.monitor_bandwidth), ]
            )

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

    def wait_for_monitor(self):
        time.sleep(self.monitor_interval)

    def send_resource_state_to_scheduler(self):
        resource_info = {'cpu': self.cpu,
                         'memory': self.memory,
                         'bandwidth': self.bandwidth,
                         'is_server': self.is_iperf3_server}
        LOGGER.info(f'[Monitor Resource] info: {resource_info}')

        data = {'device': self.local_device, 'resource': resource_info}

        http_request(self.scheduler_address,
                     method=NetworkAPIMethod.SCHEDULER_RESOURCE,
                     data={'data': json.dumps(data)})

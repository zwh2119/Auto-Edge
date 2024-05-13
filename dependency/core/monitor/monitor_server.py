from .monitor import Monitor


class MonitorServer:
    def __init__(self):
        self.monitor = Monitor()

    def run(self):
        while True:
            self.monitor.monitor_resource()
            self.monitor.send_resource_state_to_scheduler()
            self.monitor.wait_for_monitor()

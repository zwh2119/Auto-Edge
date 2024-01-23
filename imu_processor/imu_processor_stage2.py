# add base path to sys.path
import os, sys

print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.service.processor import Processor
from framework.message_queue.mqtt import MqttSubscriber, MqttPublisher
import json
import logging
import time
from mpl_toolkits.mplot3d import Axes3D
import base64
import numpy as np
import threading
from scipy.integrate import cumtrapz
import matplotlib.pyplot as plt
import io

if __name__ == '__main__':
    from imu_task import ImuTask
else:
    from .imu_task import ImuTask


class ImuProcessor2(Processor):
    def __init__(self, id: str, incoming_mq_topic: str, outgoing_mq_topic: str,
                 priority: int, tuned_parameters: dict,
                 mqtt_host: str = 'localhost', mqtt_port: int = 1883, mqtt_username: str = 'admin',
                 mqtt_password: str = 'admin'):
        super().__init__(id, incoming_mq_topic, outgoing_mq_topic, priority, tuned_parameters)
        mqtt_client_id = str(id)
        self.subscriber = MqttSubscriber(mqtt_host, mqtt_port, mqtt_username, mqtt_password,
                                         mqtt_client_id + "_subscriber")
        self.publisher = MqttPublisher(mqtt_host, mqtt_port, mqtt_username, mqtt_password,
                                       mqtt_client_id + "_publisher")
        # This will be accessed by different threads, so we need to use a lock
        self.lock = threading.Lock()
        self.local_task_queue = []

    @classmethod
    def processor_type(cls) -> str:
        return 'imu'

    @classmethod
    def processor_description(cls) -> str:
        return 'Imu processor2'

    def get_id(self) -> str:
        return self._id

    def get_incoming_mq_topic(self) -> str:
        return self._incoming_mq_topic

    def get_outgoing_mq_topic(self) -> str:
        return self._outgoing_mq_topic

    def get_priority(self) -> int:
        return self._priority

    def set_priority(self, priority: int):
        self._priority = priority

    def get_tuned_parameters(self) -> dict:
        return self._tuned_parameters

    def set_tuned_parameters(self, tuned_parameters: dict):
        self._tuned_parameters = tuned_parameters

    def get_task_from_incoming_mq(self) -> ImuTask:
        with self.lock:
            return self.local_task_queue.pop(0)

    def send_task_to_outgoing_mq(self, task: ImuTask):
        self.publisher.publish(self._outgoing_mq_topic, json.dumps(task.serialize()), qos=2)

    def run(self):
        self.subscriber.subscribe(self._incoming_mq_topic,
                                  callback=(lambda client, userdata, message: (
                                      self.lock.acquire(),
                                      self.local_task_queue.append(
                                          ImuTask.deserialize(json.loads(message.payload.decode()))),
                                      self.lock.release())),
                                  qos=2
                                  )
        self.subscriber.client.loop_start()
        self.publisher.client.loop_start()
        while True:
            if len(self.local_task_queue) > 0:
                # task = self.get_task_from_incoming_mq()
                # print(task.get_seq_id())
                # print(task.get_source_id())
                # print(task.get_data())
                # continue

                task = self.get_task_from_incoming_mq()
                # print(task.get_seq_id())
                # print(task.get_source_id())
                # print(len(task.get_data()))
                # print(task.get_priority())
                print(
                    f"Processing task {task.get_seq_id()} from source {task.get_source_id()}, task size: {len(task.get_data())}")
                # data = base64.b64decode(task.get_data().encode('utf-8'))
                task_data = json.loads(task.get_data())
                data=task_data["displacement"]
                data=np.array(data)
                # 绘制3D轨迹图
                fig = plt.figure()
                ax = fig.add_subplot(111, projection='3d')
                ax.plot3D(data[:, 0], data[:, 1], data[:, 2])
                ax.set_title('Displacement')
                # 保存为二进制
                buffer = io.BytesIO()
                plt.savefig(buffer, format='png')
                buffer.seek(0)
                base64_encoded_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
                process_result=json.dumps({"pic":base64_encoded_image})
                print(1)
                processed_task = ImuTask(process_result, task.get_seq_id(), task.get_source_id(), self.get_priority())
                self.send_task_to_outgoing_mq(processed_task)



if __name__ == '__main__':
    # parse args from cmd
    import argparse

    parser = argparse.ArgumentParser(description='Imu processor')
    parser.add_argument('--id', type=str, help='processor id')
    # parser.add_argument('--incoming_mq_topic', type=str, help='incoming message queue topic')
    # parser.add_argument('--outgoing_mq_topic', type=str, help='outgoing message queue topic')
    # parser.add_argument('--priority', type=int, help='processor priority')
    # parser.add_argument('--tuned_parameters', type=str, help='processor tuned parameters')
    args = parser.parse_args()
    id = args.id
    processor = ImuProcessor2(f'processor_stage_2_instance_{id}', 'testapp/processor_stage_1',
                              'testapp/processor_stage_2', 0, {})
    processor.run()
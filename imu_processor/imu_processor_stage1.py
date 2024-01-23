# add base path to sys.path
import os, sys

print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.service.processor import Processor
from framework.message_queue.mqtt import MqttSubscriber, MqttPublisher
import json
import base64
import numpy as np
import threading
from scipy.integrate import cumtrapz

if __name__ == '__main__':
    from imu_task import ImuTask
else:
    from .imu_task import ImuTask


class ImuProcessor1(Processor):
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
        return 'Imu processor1'

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

                R = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
                task = self.get_task_from_incoming_mq()
                # print(task.get_seq_id())
                # print(task.get_source_id())
                # print(len(task.get_data()))
                # print(task.get_priority())
                print(
                    f"Processing task {task.get_seq_id()} from source {task.get_source_id()}, task size: {len(task.get_data())}")
                # data = base64.b64decode(task.get_data().encode('utf-8'))
                data = np.frombuffer(base64.b64decode(task.get_data().encode('utf-8'))).reshape((-1, 7))
                process_result = self.getPCA4(data, R)
                # print(f"Processed result: {process_result}")
                processed_task = ImuTask(process_result, task.get_seq_id(), task.get_source_id(), self.get_priority())
                self.send_task_to_outgoing_mq(processed_task)

    def getPCA4(self, data, R):
        lpms_time = data[:, 0]
        lpms_gyro = data[:, 1:4]
        lpms_linearacc = data[:, 4:7]
        C = self.getRelativeRotation(lpms_gyro, lpms_time, R)
        linearacc_proj = self.getProjLA(lpms_linearacc, C)
        displacement = self.getDis(lpms_time, linearacc_proj)
        # 将NumPy数组转换为Python列表
        displace = displacement.tolist()
        json_data = json.dumps({"displacement": displace})
        # print(json_data)
        return json_data

    def getRelativeRotation(self, lpms_gyro, lpms_time, R):
        """
        Calculate the rotation matrix from body frame to global frame for motion data.

        Parameters:
        - lpms_gyro: Gyroscope data (angular velocity) in body frame.
        - lpms_time: Timestamps corresponding to the gyroscope data.
        - R: Initial rotation matrix.

        Returns:
        - C: Rotation matrices for each time step.
        """
        sample_num = lpms_gyro.shape[0]
        I = np.eye(3)

        # Initialize rotation matrix
        C = np.zeros((3, 3, sample_num))
        C[:, :, 0] = R

        for i in range(1, sample_num):
            w = lpms_gyro[i, :]
            wx, wy, wz = w
            t = lpms_time[i] - lpms_time[i - 1]
            B = np.array([[0, -wz * t, wy * t],
                          [wz * t, 0, -wx * t],
                          [-wy * t, wx * t, 0]])
            delta = np.linalg.norm(w * t)
            Ai = I + np.sin(delta) / delta * B + (1 - np.cos(delta)) / (delta ** 2) * np.dot(B, B)
            Ci = np.dot(C[:, :, i - 1], Ai)
            C[:, :, i] = Ci

        return C

    def getProjLA(self, watch_linearacc, C):
        """
        Rotate linear acceleration to the global frame.

        Parameters:
        - watch_linearacc: Local linear acceleration.
        - C: Rotation matrices for each time step.

        Returns:
        - linearacc_proj: Projected linear acceleration in the global frame.
        """

        linearacc_proj = np.zeros_like(watch_linearacc)
        sample_num = watch_linearacc.shape[0]

        for i in range(sample_num):
            # Get the rotation matrix from local to global frame
            Ci = C[:, :, i]

            # Get local linear acceleration
            linearacci = watch_linearacc[i, :]

            # Project current linear acceleration to global frame
            linearacc_proj[i, :] = np.dot(Ci, linearacci)

        return linearacc_proj

    def getDis(self, watch_time, linearacc_proj):
        """
        Estimate the displacement in the global frame via projected linear acceleration.

        Parameters:
        - watch_time: Timestamps corresponding to the linear acceleration data.
        - linearacc_proj: Projected linear acceleration in the global frame.

        Returns:
        - displacement: Displacement in the global frame.
        """

        watch_time = watch_time - watch_time[0]

        # Raw velocity
        velocity = np.copy(linearacc_proj)
        for i in range(3):

            velocity[:, i] = cumtrapz(linearacc_proj[:, i], watch_time[:], initial=0)

        # Calibrated velocity
        v_offset = velocity[-1, :]
        v_offset_unit = v_offset / watch_time[-1]
        v_subtract = np.outer(watch_time, v_offset_unit)
        v_calibrate = velocity - v_subtract

        # Displacement
        displacement = np.copy(v_calibrate)
        for i in range(3):
            displacement[:, i] = cumtrapz(v_calibrate[:, i], watch_time[:], initial=0)

        return displacement


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
    processor = ImuProcessor1(f'processor_stage_1_instance_{id}', '$share/python/testapp/generator',
                              'testapp/processor_stage_1', 0, {})
    processor.run()
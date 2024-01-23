# add base path to sys.path
import os
import sys

print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.service.processor import Processor
from framework.message_queue.mqtt import MqttSubscriber, MqttPublisher
import json
import base64
import numpy as np
import threading
import logmmse
import librosa

if __name__ == '__main__':
    from audio_task import AudioTask
else:
    from .audio_task import AudioTask


class AudioProcessor1(Processor):
    def __init__(self, id: str, incoming_mq_topic: str, outgoing_mq_topic: str,
                 priority: int, tuned_parameters: dict,
                 mqtt_host: str = '138.3.208.203', mqtt_port: int = 1883, mqtt_username: str = 'admin',
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
        return 'audio'

    @classmethod
    def processor_description(cls) -> str:
        return 'Audio processor1'

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

    def get_task_from_incoming_mq(self) -> AudioTask:
        with self.lock:
            return self.local_task_queue.pop(0)

    def send_task_to_outgoing_mq(self, task: AudioTask):
        self.publisher.publish(self._outgoing_mq_topic, json.dumps(task.serialize()), qos=2)

    def run(self):
        self.subscriber.subscribe(self._incoming_mq_topic,
                                  callback=(lambda client, userdata, message: (
                                      self.lock.acquire(),
                                      self.local_task_queue.append(
                                          AudioTask.deserialize(json.loads(message.payload.decode()))),
                                      self.lock.release())),
                                  qos=2
                                  )
        self.subscriber.client.loop_start()
        self.publisher.client.loop_start()
        while True:
            if len(self.local_task_queue) > 0:
                task = self.get_task_from_incoming_mq()
                print(task.get_seq_id())
                print(task.get_source_id())
                print(len(task.get_data()))
                print(task.get_priority())
                print(f"Processing task {task.get_seq_id()} from source {task.get_source_id()}")
                data = base64.b64decode(task.get_data().encode('utf-8'))

                if task.get_metadata()['resample_rate'] != 0:
                    data = self.resample(data, task.get_metadata()['framerate'], task.get_metadata()['resample_rate'])

                process_result = self.remove_noise(data, task.get_metadata()["framerate"] if task.get_metadata()[
                                                                                                 "resample_rate"] == 0 else
                task.get_metadata()["resample_rate"], task.get_metadata()['sampwidth'], task.get_metadata()['nchannels'])
                # print(f"Processed result: {process_result}")

                base64_process_result = base64.b64encode(process_result).decode('utf-8')
                processed_task = AudioTask(base64_process_result, task.get_seq_id(), task.get_source_id(),
                                           self.get_priority(), task.get_metadata())
                self.send_task_to_outgoing_mq(processed_task)

    def resample(self, data, framerate, resample_rate):
        if framerate <= resample_rate:
            print("framerate <= resample_rate")
            return data
        else:
            data = np.frombuffer(data, dtype=np.short)  # 将音频转换为数组
            return librosa.resample(data.astype(np.float32), orig_sr=framerate, target_sr=resample_rate).astype(
                np.short).tobytes()

    def remove_noise(self, data, framerate, sampwidth, nchannels):
        if sampwidth == 2:
            data = np.frombuffer(data, dtype=np.short)  # 将音频转换为数组
            data = logmmse.logmmse(data=data, sampling_rate=framerate, noise_threshold=0.05)
            if nchannels == 2:
                data = (data[::2] + data[1::2]) / 2
            return data.astype(np.short).tobytes()
        elif sampwidth == 3:
            pass


if __name__ == '__main__':
    # parse args from cmd
    import argparse

    parser = argparse.ArgumentParser(description='Audio processor')
    parser.add_argument('--id', type=str, default=1, help='processor id')
    # parser.add_argument('--incoming_mq_topic', type=str, help='incoming message queue topic')
    # parser.add_argument('--outgoing_mq_topic', type=str, help='outgoing message queue topic')
    # parser.add_argument('--priority', type=int, help='processor priority')
    # parser.add_argument('--tuned_parameters', type=str, help='processor tuned parameters')
    args = parser.parse_args()
    id = args.id
    processor = AudioProcessor1(f'processor_stage_1_instance_{id}', '$share/python/testapp/generator',
                                'testapp/processor_stage_1', 0, {})
    processor.run()
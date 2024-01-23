# add base path to sys.path
import os
import sys

import librosa

print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from framework.service.processor import Processor
from framework.message_queue.mqtt import MqttSubscriber, MqttPublisher
import json
import time
import threading
import base64
import numpy as np
import torch

if __name__ == '__main__':
    from audio_task import AudioTask
else:
    from .audio_task import AudioTask

model_path = 'model.pth'
device = torch.device("cuda:0" if (torch.cuda.is_available()) else "cpu")
model = torch.jit.load(model_path, map_location=device)
model.to(device)
model.eval()

sound_categories = [
    "Air Conditioner (空调)",
    "Car Horn (汽车喇叭)",
    "Children Playing (儿童游玩)",
    "Dog Bark (狗叫)",
    "Drilling (钻孔)",
    "Engine Idling (引擎怠速)",
    "Gun Shot (枪声)",
    "Jackhammer (挖掘机)",
    "Siren (警报声)",
    "Street Music (街头音乐)"
]


class AudioProcessor2(Processor):
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
        return 'Audio processor2'

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
                print(
                    f"Processing task {task.get_seq_id()} from source {task.get_source_id()}, task size: {len(task.get_data())}")
                task_data = base64.b64decode(task.get_data().encode('utf-8'))
                mode = task.get_metadata()["mode"]
                if mode == 1:
                    pass
                elif mode == 2:
                    index, time = self.infer(task_data, task.get_metadata()["framerate"] if task.get_metadata()[
                                                                                                "resample_rate"] == 0 else
                    task.get_metadata()["resample_rate"])
                    print("time: ", time)
                    # index = 4
                    task.get_metadata().update({"category": str(index) + '-' + sound_categories[index]})

                processed_task = AudioTask(task.get_data(), task.get_seq_id(), task.get_source_id(),
                                           self.get_priority(),
                                           json.dumps(task.get_metadata()))
                print(task.get_metadata())
                # print(json.dumps(task.get_metadata()))
                self.send_task_to_outgoing_mq(processed_task)

    def infer(self, data, framerate):
        data = self.load_data(data, framerate)
        data = torch.tensor(data, dtype=torch.float32, device=device)
        # 执行预测
        # 开始计时
        time1 = time.time() * 1000
        output = model(data)
        # 结束计时
        time2 = time.time() * 1000
        result = torch.nn.functional.softmax(output)
        result = result.data.cpu().numpy()
        # print(result)
        # 显示图片并输出结果最大的label
        lab = np.argsort(result)[0][-1]
        return lab, time2 - time1

    def load_data(self, data, framerate):
        data = np.frombuffer(data, dtype=np.short) / np.iinfo(np.short).max
        data = librosa.resample(data, orig_sr=framerate, target_sr=16000)
        spec_mag = librosa.feature.melspectrogram(y=data * 1.0, sr=16000, hop_length=256).astype(np.float32)
        mean = np.mean(spec_mag, 0, keepdims=True)
        std = np.std(spec_mag, 0, keepdims=True)
        spec_mag = (spec_mag - mean) / (std + 1e-5)
        spec_mag = spec_mag[np.newaxis, np.newaxis, :]
        print(spec_mag.shape)
        # [1, 1, 128, 251] -> [1, 3, 128, 251]
        spec_mag = np.repeat(spec_mag, 3, axis=1)

        return spec_mag


if __name__ == '__main__':
    # parse args from cmd
    import argparse

    parser = argparse.ArgumentParser(description='Audio processor')
    parser.add_argument('--id', type=str, help='processor id')
    # parser.add_argument('--incoming_mq_topic', type=str, help='incoming message queue topic')
    # parser.add_argument('--outgoing_mq_topic', type=str, help='outgoing message queue topic')
    # parser.add_argument('--priority', type=int, help='processor priority')
    # parser.add_argument('--tuned_parameters', type=str, help='processor tuned parameters')
    args = parser.parse_args()
    id = args.id
    processor = AudioProcessor2(f'processor_stage_2_instance_{id}', '$share/python/testapp/processor_stage_1',
                                'testapp/processor_stage_2', 0, {})
    processor.run()
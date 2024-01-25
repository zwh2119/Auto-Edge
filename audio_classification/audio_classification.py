# add base path to sys.path
import os
import sys

import librosa

print(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time

import numpy as np
import torch

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


class AudioClassification:
    def __init__(self):
        pass

    def run(self, data):

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


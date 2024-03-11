import librosa

import json
import time

import numpy as np
import torch
from torchvision.models import resnet34
from log import LOGGER


class AudioClassification:
    def __init__(self, cfg):
        self.sound_categories = [
            "Other (其他声音)"
            "Car Horn (喇叭声)",
            "Drilling (钻孔声)",
            "Engine Idling (引擎声)",
            "Jackhammer (重型机械声)",
            "Siren (警报声)",
        ]

        self.num_class = 10

        self.model_path = cfg['model_path']
        self.device = torch.device(cfg['device'])

        LOGGER.debug(f'loading model')

        self.model = self.load_model()

    def __call__(self, data, metadata):
        LOGGER.debug('start infer ..')
        index, consuming_time = self.infer(data, metadata["framerate"] if metadata["resample_rate"] == 0 else metadata[
            "resample_rate"])
        index = index.item()
        index = [0, 1, 0, 0, 2, 3, 0, 4, 5, 0][index]

        output_ctx = {}
        output_ctx['parameters'] = {}
        output_ctx['parameters']['obj_num'] = []
        output_ctx['parameters']['obj_num'].append(index)

        return output_ctx

    def infer(self, data, framerate):
        data = self.load_data(data, framerate)
        data = torch.tensor(data, dtype=torch.float32, device=self.device)
        # LOGGER.debug(f'data: {data}')
        # 执行预测
        # 开始计时
        time1 = time.time() * 1000
        LOGGER.debug('put in model')
        output = self.model(data)
        LOGGER.debug('get output from model')
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
        # TODO: to speed up, resample the data to 1600fps
        # data = librosa.resample(data, orig_sr=framerate, target_sr=16000)
        spec_mag = librosa.feature.melspectrogram(y=data * 1.0, sr=16000, hop_length=256).astype(np.float32)
        mean = np.mean(spec_mag, 0, keepdims=True)
        std = np.std(spec_mag, 0, keepdims=True)
        spec_mag = (spec_mag - mean) / (std + 1e-5)
        spec_mag = spec_mag[np.newaxis, np.newaxis, :]

        # print(spec_mag.shape)
        # [1, 1, 128, 251] -> [1, 3, 128, 251]
        spec_mag = np.repeat(spec_mag, 3, axis=1)

        return spec_mag

    def load_model(self):
        LOGGER.debug(f'device: {type(self.device)}   {self.device}')
        model = resnet34(num_classes=self.num_class)
        model.load_state_dict(torch.load(self.model_path))
        LOGGER.debug('load model')
        model.to(self.device)
        LOGGER.debug('transform model to target device')
        model.eval()
        LOGGER.debug('evaluation mode of model')
        LOGGER.debug('load model completed ..')
        return model

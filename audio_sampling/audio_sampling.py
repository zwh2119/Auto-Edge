
import numpy as np

import logmmse
import librosa


class AudioSampling:
    def __init__(self):
        pass

    def __call__(self, data, metadata):

        if metadata['resample_rate'] != 0:
            data = self.resample(data, metadata['framerate'], metadata['resample_rate'])

        process_result = self.remove_noise(data, metadata["framerate"] if metadata['resample_rate'] == 0 else
        metadata["resample_rate"], metadata['sampwidth'], metadata['nchannels'])
        return process_result

    def resample(self, data, framerate, resample_rate):
        if framerate <= resample_rate:
            return data
        else:
            data = np.frombuffer(data, dtype=np.short)  # 将音频转换为数组
            return librosa.resample(data.astype(np.float32), orig_sr=framerate, target_sr=resample_rate).astype(
                np.short).tobytes()

    def remove_noise(self, data, framerate, sampwidth, nchannels):
        if sampwidth == 2:
            data = np.frombuffer(data, dtype=np.short)  # 将音频转换为数组
            # data = logmmse.logmmse(data=data, sampling_rate=framerate, noise_threshold=0.05)
            if nchannels == 2:
                data = (data[::2] + data[1::2]) / 2
            return data.astype(np.short).tobytes()
        elif sampwidth == 3:
            pass

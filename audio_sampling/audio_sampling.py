
import base64
import numpy as np
import threading
import logmmse
import librosa


class AudioSampling:
    def __init__(self):
        pass

    def __cal__(self, data):

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


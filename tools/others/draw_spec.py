import io
import wave
import librosa
import numpy as np
from PIL import Image
from matplotlib import pyplot as plt


def draw_spec(data, framerate, nchannels):
    def cal_norm(nparray):
        # [-1, 1]
        return 2 * (nparray - np.min(nparray)) / (np.max(nparray) - np.min(nparray)) - 1

    databuffer = np.frombuffer(data, dtype=np.short)
    if nchannels == 2:
        databuffer = (databuffer[::2] + databuffer[1::2]) / 2

    window_size = int(0.05 * framerate)
    overlap = int(window_size * (1 - 0.75))
    n_fft = 4096

    stft = librosa.stft(databuffer.astype(np.float32), n_fft=n_fft, hop_length=overlap, win_length=window_size)

    # 转换为分贝 (dB) 单位
    log_spectrogram = librosa.amplitude_to_db(np.abs(stft))
    # 归一化为 [-1, 1]
    log_spectrogram = cal_norm(log_spectrogram)

    # 画出频谱图
    librosa.display.specshow(log_spectrogram, sr=framerate, win_length=window_size, hop_length=overlap,
                             x_axis='time', y_axis='linear')
    # 添加颜色条
    plt.colorbar(format='%+2.0f', ticks=[-1, 1])
    # plt.show()

    # 创建内存缓冲区
    imgbuffer = io.BytesIO()
    # 保存图像到内存缓冲区
    plt.savefig(imgbuffer, format='png')
    # 打开图像
    image = Image.open(imgbuffer)
    # 显示图像
    image.show()


if __name__ == '__main__':
    '''
    README
    此文件用于绘制音频频谱图
    使用时，直接导入调用 draw_spec(data, framerate) 函数即可
    可以将频谱图输出为数据流，用于在前端显示
    具体可参考 imgbuffer = io.BytesIO() 部分
    '''

    path = 'D:\project\\voice_demo\data\\16-9-siren.wav'
    f = wave.open(path, "r")
    params = f.getparams()
    nchannels, sampwidth, framerate, nframes = params[:4]  # 声道数，位数/8，采样频率，采样点数
    print("nchannels:", nchannels, "sampwidth:", sampwidth, "framerate:", framerate, "nframes:", nframes)
    data = f.readframes(nframes)
    draw_spec(data, framerate)

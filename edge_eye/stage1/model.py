import torch.nn as nn
import torch.nn.functional as F


class Net(nn.Module): # 2
    def __init__(self, upscale_factor):
        super(Net, self).__init__()

        self.conv1 = nn.Conv2d(1, 64, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(64, 32, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(32, 1 * (upscale_factor ** 2), (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)

    def forward(self, x):
        x = F.tanh(self.conv1(x))
        x = F.tanh(self.conv2(x))
        x = F.sigmoid(self.pixel_shuffle(self.conv3(x)))
        return x

class Net_Compressed(nn.Module): # 2
    def __init__(self, upscale_factor):
        super(Net_Compressed, self).__init__()

        self.conv1 = nn.Conv2d(1, 16, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(16, 8, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(8, 1 * (upscale_factor ** 2), (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)

    def forward(self, x):
        x = F.tanh(self.conv1(x))
        x = F.tanh(self.conv2(x))
        x = F.sigmoid(self.pixel_shuffle(self.conv3(x)))
        return x

class Net_Grow(nn.Module): # 2
    def __init__(self, upscale_factor):
        super(Net_Grow, self).__init__()

        self.conv1 = nn.Conv2d(1, 2, (5, 5), (1, 1), (2, 2))
        self.conv2 = nn.Conv2d(2, 3, (3, 3), (1, 1), (1, 1))
        self.conv3 = nn.Conv2d(3, 1 * (upscale_factor ** 2), (3, 3), (1, 1), (1, 1))
        self.pixel_shuffle = nn.PixelShuffle(upscale_factor)

    def forward(self, x):
        x = F.tanh(self.conv1(x))
        x = F.tanh(self.conv2(x))
        x = F.sigmoid(self.pixel_shuffle(self.conv3(x)))
        return x

if __name__ == "__main__":
    model = Net(upscale_factor=2)
    model_1 = Net_Compressed(upscale_factor=2)
    model_2 = Net_Grow(upscale_factor=2)
    print(model, model_1, model_2)
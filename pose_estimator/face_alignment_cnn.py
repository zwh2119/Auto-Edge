
import numpy as np
import torch
from torch.autograd import Variable
from torchvision import transforms
import torch.backends.cudnn as cudnn
import torchvision
import torch.nn.functional as F
from PIL import Image

import hopenet
import hopenetlite_v2

import os


def use_gpu(dev):
    ret = False

    if dev[:4] == 'cuda':
        if torch.cuda.is_available():
            ret = True
            # print('using gpu ({})'.format(dev))
        else:
            print('torch.cuda.is_available() == False')
    else:
        print('device ({}) is not cuda:*'.format(dev))

    return ret


class FaceAlignmentCNN:

    def __init__(self, args):

        # for loading model at relative path
        ori_dir = os.getcwd()
        os.chdir(os.path.dirname(__file__))

        cudnn.enabled = True

        self.__gpu = args['device']
        model_path = args['model_path']

        print('[{}] Loading model from {}...'.format(__name__, args['model_path']))

        if not args['lite_version']:
            self.__model = hopenet.Hopenet(torchvision.models.resnet.Bottleneck, [3, 4, 6, 3], 66)
        else:
            self.__model = hopenetlite_v2.HopeNetLite()  # lite version

        saved_state_dict = torch.load(model_path, map_location=torch.device('cpu'))
        self.__model.load_state_dict(saved_state_dict)

        # image preprocess
        self.__transformations = transforms.Compose([transforms.Resize(224),
                                                     transforms.CenterCrop(224), transforms.ToTensor(),
                                                     transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                                                          std=[0.229, 0.224, 0.225])])

        if use_gpu(self.__gpu):
            self.__model.cuda(self.__gpu)
        else:
            self.__model.eval()

        idx_tensor = [idx for idx in range(66)]
        if use_gpu(self.__gpu):
            self.__idx_tensor = torch.FloatTensor(idx_tensor).cuda(self.__gpu)
        else:
            self.__idx_tensor = torch.FloatTensor(idx_tensor)

        self.__batch_size = args['batch_size']

        # for loading model at relative path
        os.chdir(ori_dir)

    async def __call__(self, images, boxes):

        output_ctx = {'result': [], 'probs': [], 'parameters': {}}
        output_ctx['parameters']['total'] = []
        output_ctx['parameters']['up'] = []

        for image, bbox in zip(images, boxes):
            height, width, _ = image.shape

            up, total, threshold = 0, len(bbox), -10

            head_pose = []
            for x_min, y_min, x_max, y_max in bbox:

                x_min = int(max(x_min, 0))
                y_min = int(max(y_min, 0))
                x_max = int(min(width, x_max))
                y_max = int(min(height, y_max))

                face = Image.fromarray(image[y_min:y_max, x_min:x_max])
                face = self.__transformations(face)
                face = face.view(1, face.shape[0], face.shape[1], face.shape[2])

                if use_gpu(self.__gpu):
                    face = Variable(face).cuda(self.__gpu)
                else:
                    face = Variable(face)

                yaw, pitch, roll = self.__model(face)
                yaw_predicted = F.softmax(yaw, dim=1)
                pitch_predicted = F.softmax(pitch, dim=1)
                roll_predicted = F.softmax(roll, dim=1)
                yaw_predicted = torch.sum(yaw_predicted.data[0] * self.__idx_tensor) * 3 - 99
                pitch_predicted = torch.sum(pitch_predicted.data[0] * self.__idx_tensor) * 3 - 99
                roll_predicted = torch.sum(roll_predicted.data[0] * self.__idx_tensor) * 3 - 99
                head_pose.append(
                    [yaw_predicted, pitch_predicted, roll_predicted, (x_min + x_max) / 2, (y_min + y_max) / 2,
                     (y_max - y_min) / 2])

                if pitch_predicted > threshold:
                    up += 1

            if use_gpu(self.__gpu):
                head_pose = torch.Tensor(head_pose).cpu().tolist()
            else:
                head_pose = np.array(head_pose, dtype=np.float32).tolist()

            output_ctx['result'].append(head_pose)
            output_ctx['parameters']['total'].append(total)
            output_ctx['parameters']['up'].append(up)

        return output_ctx

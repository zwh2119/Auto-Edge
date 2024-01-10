from vision.ssd.config.fd_config import define_img_size
from vision.ssd.mb_tiny_fd import create_mb_tiny_fd, create_mb_tiny_fd_predictor
from vision.ssd.mb_tiny_RFB_fd import create_Mb_Tiny_RFB_fd, create_Mb_Tiny_RFB_fd_predictor

import os
import sys


class FaceDetection:

    def __init__(self, args):

        self.preload_image_path = 'preload.jpg'
        self.preload_cycle = 10

        # must put define_img_size() before 'import create_mb_tiny_fd, create_mb_tiny_fd_predictor'
        ori_dir = os.getcwd()
        os.chdir(os.path.dirname(__file__) or '.')
        print('{}'.format(os.getcwd()))

        define_img_size(args['input_size'])
        label = 'models/voc-model-labels.txt'
        class_names = [name.strip() for name in open(label).readlines()]

        if args['net_type'] == 'mb_tiny_fd':
            model_path = 'models/pretrained/Mb_Tiny_FD_train_input_320.pth'
            net = create_mb_tiny_fd(len(class_names), is_test=True, device=args['device'])
            self.__predictor = create_mb_tiny_fd_predictor(
                net,
                candidate_size=args['candidate_size'],
                device=args['device'])
        elif args['net_type'] == 'mb_tiny_RFB_fd':
            model_path = 'models/pretrained/Mb_Tiny_RFB_FD_train_input_320.pth'
            # model_path = "models/pretrained/Mb_Tiny_RFB_FD_train_input_640.pth"
            net = create_Mb_Tiny_RFB_fd(len(class_names), is_test=True, device=args['device'])
            self.__predictor = create_Mb_Tiny_RFB_fd_predictor(
                net,
                candidate_size=args['candidate_size'],
                device=args['device'])
        else:
            print('[{}] The net type is wrong!'.format(__name__))
            sys.exit(1)

        self.__args = args
        net.load(model_path)

        os.chdir(ori_dir)

    async def __call__(self, images):
        assert type(images) is list

        output_ctx = {'result': [], 'probs': [], 'parameters': {}}
        output_ctx['parameters']['obj_num'] = []
        output_ctx['parameters']['obj_size'] = []

        for image in images:
            boxes, labels, probs = self.__predictor.predict(image,
                                                            self.__args['candidate_size'] / 2,
                                                            self.__args['threshold'])

            height, width, _ = image.shape
            # print('[{}] len(boxes)={}'.format(__name__, len(boxes)))
            faces = []
            size = 0
            num = len(boxes)
            for x_min, y_min, x_max, y_max in boxes:
                x_min = int(max(x_min, 0))
                y_min = int(max(y_min, 0))
                x_max = int(min(width, x_max))
                y_max = int(min(height, y_max))

                faces.append([x_min, y_min, x_max, y_max])
                size += (y_max - y_min) * (x_max - x_min)
            output_ctx['result'].append(faces)
            output_ctx['parameters']['obj_num'].append(num)
            output_ctx['parameters']['obj_size'].append(size / num if num!=0 else 0)
            output_ctx['probs'].append([probs[i].item() for i in range(probs.size(0))])

        return output_ctx

    def preload(self):
        input_image = cv2.imread(self.preload_image_path)
        for i in range(self.preload_cycle):
            self.__predictor.predict(input_image,
                                     self.__args['candidate_size'] / 2,
                                     self.__args['threshold'])


if __name__ == '__main__':
    args_ = {
        'net_type': 'mb_tiny_RFB_fd',
        'input_size': 480,
        'threshold': 0.7,
        'candidate_size': 1500,
        'device': 'cpu'
        # 'device': 'cuda:0'
    }

    detector = FaceDetection(args_)

    import cv2

    video_cap = cv2.VideoCapture('input/input.mp4')

    ret, frame = video_cap.read()

    while ret:
        ret, frame = video_cap.read()

        input_ctx = dict()
        input_ctx['image'] = frame
        detector(input_ctx)
        print('detect one frame')

import argparse
import ctypes
import json
import os.path
import time

import numpy as np

import pycuda.autoinit
import pycuda.driver as cuda
import tensorrt as trt

import cv2
from tqdm import tqdm


def parse_opt(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', type=str, help='model path or triton URL')
    parser.add_argument('--plugin_library', type=str)
    parser.add_argument('--batch_size', type=int, default=1)
    parser.add_argument('--device', default=0, type=int, help='cuda device, i.e. 0,1,2')
    parser.add_argument('--conf_thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou_thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--len_one_result', type=int, default=38)
    parser.add_argument('--len_all_result', type=int, default=38001)
    parser.add_argument('--warm_up_turns', type=int, default=20)

    opt = parser.parse_args(args)
    # print_args(vars(opt))
    return opt


class CarDetection:

    def __init__(self, args):
        # write code to change the args dict to command line args
        args_list = []
        for k, v in args.items():
            args[k] = '--' + k
            args_list.append(args[k])
            args_list.append(str(v))
        args = args_list

        self.opt = parse_opt(args)

        ctypes.CDLL(self.opt.plugin_library)

        self.ctx = cuda.Device(self.opt.device).make_context()
        stream = cuda.Stream()
        TRT_LOGGER = trt.Logger(trt.Logger.INFO)
        runtime = trt.Runtime(TRT_LOGGER)
        engine_file_path = self.opt.weights

        with open(engine_file_path, "rb") as f:
            engine = runtime.deserialize_cuda_engine(f.read())
        context = engine.create_execution_context()

        host_inputs = []
        cuda_inputs = []
        host_outputs = []
        cuda_outputs = []
        bindings = []

        for binding in engine:
            # print('bingding:', binding, engine.get_binding_shape(binding))
            size = trt.volume(engine.get_binding_shape(binding)) * engine.max_batch_size
            dtype = trt.nptype(engine.get_binding_dtype(binding))
            # Allocate host and device buffers
            host_mem = cuda.pagelocked_empty(size, dtype)
            cuda_mem = cuda.mem_alloc(host_mem.nbytes)
            # Append the device buffer to device bindings.
            bindings.append(int(cuda_mem))
            # Append to the appropriate list.
            if engine.binding_is_input(binding):
                self.input_w = engine.get_binding_shape(binding)[-1]
                self.input_h = engine.get_binding_shape(binding)[-2]
                host_inputs.append(host_mem)
                cuda_inputs.append(cuda_mem)
            else:
                host_outputs.append(host_mem)
                cuda_outputs.append(cuda_mem)

        self.stream = stream
        self.context = context
        self.engine = engine
        self.host_inputs = host_inputs
        self.cuda_inputs = cuda_inputs
        self.host_outputs = host_outputs
        self.cuda_outputs = cuda_outputs
        self.bindings = bindings
        self.batch_size = engine.max_batch_size
        # print('batch_size:', self.batch_size)

        self.warm_up_turns = self.opt.warm_up_turns

        self.conf_thres = self.opt.conf_thres
        self.iou_thres = self.opt.iou_thres
        self.len_one_result = self.opt.len_one_result
        self.len_all_result = self.opt.len_all_result

        self.categories = ["person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
                           "traffic light",
                           "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat", "dog", "horse",
                           "sheep",
                           "cow",
                           "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella", "handbag", "tie", "suitcase",
                           "frisbee",
                           "skis", "snowboard", "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
                           "surfboard",
                           "tennis racket", "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana",
                           "apple",
                           "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
                           "couch",
                           "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
                           "keyboard",
                           "cell phone",
                           "microwave", "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase", "scissors",
                           "teddy bear",
                           "hair drier", "toothbrush"]

        self.target_categories = ["car", "bus", "truck"]

        self.warm_up()  # warmup

    def warm_up(self):
        for i in range(self.warm_up_turns):
            im = np.zeros([self.batch_size, self.input_h, self.input_w, 3], dtype=np.uint8)
            self.infer(im)
            del im

    def __del__(self):
        self.destroy()

    def destroy(self):
        # Remove any context from the top of the context stack, deactivating it.
        self.ctx.pop()

    def preprocess_image(self, raw_bgr_image):
        """
        description: Convert BGR image to RGB,
                     resize and pad it to target size, normalize to [0,1],
                     transform to NCHW format.
        param:
            input_image_path: str, image path
        return:
            image:  the processed image
            image_raw: the original image
            h: original height
            w: original width
        """
        image_raw = raw_bgr_image
        h, w, c = image_raw.shape
        image = cv2.cvtColor(image_raw, cv2.COLOR_BGR2RGB)
        # Calculate widht and height and paddings
        r_w = self.input_w / w
        r_h = self.input_h / h
        if r_h > r_w:
            tw = self.input_w
            th = int(r_w * h)
            tx1 = tx2 = 0
            ty1 = int((self.input_h - th) / 2)
            ty2 = self.input_h - th - ty1
        else:
            tw = int(r_h * w)
            th = self.input_h
            tx1 = int((self.input_w - tw) / 2)
            tx2 = self.input_w - tw - tx1
            ty1 = ty2 = 0
        # Resize the image with long side while maintaining ratio
        image = cv2.resize(image, (tw, th))
        # Pad the short side with (128,128,128)

        image = cv2.copyMakeBorder(
            image, ty1, ty2, tx1, tx2, cv2.BORDER_CONSTANT, None, (128, 128, 128)
        )

        image = image.astype(np.float32)
        # Normalize to [0,1]
        image /= 255.0
        # HWC to CHW format:
        image = np.transpose(image, [2, 0, 1])
        # CHW to NCHW format
        image = np.expand_dims(image, axis=0)

        # Convert the image to row-major order, also known as "C order":
        image = np.ascontiguousarray(image)
        return image, image_raw, h, w

    def xywh2xyxy(self, origin_h, origin_w, x):
        """
        description:    Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
        param:
            origin_h:   height of original image
            origin_w:   width of original image
            x:          A boxes numpy, each row is a box [center_x, center_y, w, h]
        return:
            y:          A boxes numpy, each row is a box [x1, y1, x2, y2]
        """
        y = np.zeros_like(x)
        r_w = self.input_w / origin_w
        r_h = self.input_h / origin_h
        if r_h > r_w:
            y[:, 0] = x[:, 0] - x[:, 2] / 2
            y[:, 2] = x[:, 0] + x[:, 2] / 2
            y[:, 1] = x[:, 1] - x[:, 3] / 2 - (self.input_h - r_w * origin_h) / 2
            y[:, 3] = x[:, 1] + x[:, 3] / 2 - (self.input_h - r_w * origin_h) / 2
            y /= r_w
        else:
            y[:, 0] = x[:, 0] - x[:, 2] / 2 - (self.input_w - r_h * origin_w) / 2
            y[:, 2] = x[:, 0] + x[:, 2] / 2 - (self.input_w - r_h * origin_w) / 2
            y[:, 1] = x[:, 1] - x[:, 3] / 2
            y[:, 3] = x[:, 1] + x[:, 3] / 2
            y /= r_h

        return y

    def post_process(self, output, origin_h, origin_w):
        """
        description: postprocess the prediction
        param:
            output:     A numpy likes [num_boxes,cx,cy,w,h,conf,cls_id, cx,cy,w,h,conf,cls_id, ...]
            origin_h:   height of original image
            origin_w:   width of original image
        return:
            result_boxes: finally boxes, a boxes numpy, each row is a box [x1, y1, x2, y2]
            result_scores: finally scores, a numpy, each element is the score correspoing to box
            result_classid: finally classid, a numpy, each element is the classid correspoing to box
        """
        # Get the num of boxes detected
        num = int(output[0])
        # Reshape to a two dimentional ndarray
        pred = np.reshape(output[1:], (-1, self.len_one_result))[:num, :]
        pred = pred[:, :6]
        # Do nms
        boxes = self.non_max_suppression(pred, origin_h, origin_w, conf_thres=self.conf_thres, nms_thres=self.iou_thres)
        result_boxes = boxes[:, :4] if len(boxes) else np.array([])
        result_scores = boxes[:, 4] if len(boxes) else np.array([])
        result_classid = boxes[:, 5] if len(boxes) else np.array([])
        return result_boxes, result_scores, result_classid

    def bbox_iou(self, box1, box2, x1y1x2y2=True):
        """
        description: compute the IoU of two bounding boxes
        param:
            box1: A box coordinate (can be (x1, y1, x2, y2) or (x, y, w, h))
            box2: A box coordinate (can be (x1, y1, x2, y2) or (x, y, w, h))
            x1y1x2y2: select the coordinate format
        return:
            iou: computed iou
        """
        if not x1y1x2y2:
            # Transform from center and width to exact coordinates
            b1_x1, b1_x2 = box1[:, 0] - box1[:, 2] / 2, box1[:, 0] + box1[:, 2] / 2
            b1_y1, b1_y2 = box1[:, 1] - box1[:, 3] / 2, box1[:, 1] + box1[:, 3] / 2
            b2_x1, b2_x2 = box2[:, 0] - box2[:, 2] / 2, box2[:, 0] + box2[:, 2] / 2
            b2_y1, b2_y2 = box2[:, 1] - box2[:, 3] / 2, box2[:, 1] + box2[:, 3] / 2
        else:
            # Get the coordinates of bounding boxes
            b1_x1, b1_y1, b1_x2, b1_y2 = box1[:, 0], box1[:, 1], box1[:, 2], box1[:, 3]
            b2_x1, b2_y1, b2_x2, b2_y2 = box2[:, 0], box2[:, 1], box2[:, 2], box2[:, 3]

        # Get the coordinates of the intersection rectangle
        inter_rect_x1 = np.maximum(b1_x1, b2_x1)
        inter_rect_y1 = np.maximum(b1_y1, b2_y1)
        inter_rect_x2 = np.minimum(b1_x2, b2_x2)
        inter_rect_y2 = np.minimum(b1_y2, b2_y2)
        # Intersection area
        inter_area = np.clip(inter_rect_x2 - inter_rect_x1 + 1, 0, None) * \
                     np.clip(inter_rect_y2 - inter_rect_y1 + 1, 0, None)
        # Union Area
        b1_area = (b1_x2 - b1_x1 + 1) * (b1_y2 - b1_y1 + 1)
        b2_area = (b2_x2 - b2_x1 + 1) * (b2_y2 - b2_y1 + 1)

        iou = inter_area / (b1_area + b2_area - inter_area + 1e-16)

        return iou

    def non_max_suppression(self, prediction, origin_h, origin_w, conf_thres=0.5, nms_thres=0.4):
        """
        description: Removes detections with lower object confidence score than 'conf_thres' and performs
        Non-Maximum Suppression to further filter detections.
        param:
            prediction: detections, (x1, y1, x2, y2, conf, cls_id)
            origin_h: original image height
            origin_w: original image width
            conf_thres: a confidence threshold to filter detections
            nms_thres: a iou threshold to filter detections
        return:
            boxes: output after nms with the shape (x1, y1, x2, y2, conf, cls_id)
        """
        # Get the boxes that score > CONF_THRESH
        boxes = prediction[prediction[:, 4] >= conf_thres]
        # Trandform bbox from [center_x, center_y, w, h] to [x1, y1, x2, y2]
        boxes[:, :4] = self.xywh2xyxy(origin_h, origin_w, boxes[:, :4])
        # clip the coordinates
        boxes[:, 0] = np.clip(boxes[:, 0], 0, origin_w - 1)
        boxes[:, 2] = np.clip(boxes[:, 2], 0, origin_w - 1)
        boxes[:, 1] = np.clip(boxes[:, 1], 0, origin_h - 1)
        boxes[:, 3] = np.clip(boxes[:, 3], 0, origin_h - 1)
        # Object confidence
        confs = boxes[:, 4]
        # Sort by the confs
        boxes = boxes[np.argsort(-confs)]
        # Perform non-maximum suppression
        keep_boxes = []
        while boxes.shape[0]:
            large_overlap = self.bbox_iou(np.expand_dims(boxes[0, :4], 0), boxes[:, :4]) > nms_thres
            label_match = boxes[0, -1] == boxes[:, -1]
            # Indices of boxes with lower confidence scores, large IOUs and matching labels
            invalid = large_overlap & label_match
            keep_boxes += [boxes[0]]
            boxes = boxes[~invalid]
        boxes = np.stack(keep_boxes, 0) if len(keep_boxes) else np.array([])
        return boxes

    def infer(self, raw_image_generator):
        # Make self the active context, pushing it on top of the context stack.
        self.ctx.push()

        # Restore
        stream = self.stream
        context = self.context
        engine = self.engine
        host_inputs = self.host_inputs
        cuda_inputs = self.cuda_inputs
        host_outputs = self.host_outputs
        cuda_outputs = self.cuda_outputs
        bindings = self.bindings
        # Do image preprocess
        batch_image_raw = []
        batch_origin_h = []
        batch_origin_w = []
        batch_input_image = np.empty(shape=[self.batch_size, 3, self.input_h, self.input_w])

        for i, image_raw in enumerate(raw_image_generator):
            input_image, image_raw, origin_h, origin_w = self.preprocess_image(image_raw)
            batch_image_raw.append(image_raw)
            batch_origin_h.append(origin_h)
            batch_origin_w.append(origin_w)

            np.copyto(batch_input_image[i], input_image)

        batch_input_image = np.ascontiguousarray(batch_input_image)

        # Copy input image to host buffer
        np.copyto(host_inputs[0], batch_input_image.ravel())

        # Transfer input data  to the GPU.
        cuda.memcpy_htod_async(cuda_inputs[0], host_inputs[0], stream)

        # Run inference.
        context.execute_async(batch_size=self.batch_size, bindings=bindings, stream_handle=stream.handle)

        # Transfer predictions back from the GPU.
        cuda.memcpy_dtoh_async(host_outputs[0], cuda_outputs[0], stream)
        # Synchronize the stream
        stream.synchronize()

        # Remove any context from the top of the context stack, deactivating it.
        self.ctx.pop()

        # Here we use the first row of output in that batch_size = 1
        output = host_outputs[0]

        output_ctx = {'result': [], 'parameters': {}, 'probs': []}
        output_ctx['parameters']['obj_num'] = []
        output_ctx['parameters']['obj_size'] = []

        # Do postprocess
        for i in range(self.batch_size):
            result_boxes, result_scores, result_classid = self.post_process(
                output[i * self.len_all_result: (i + 1) * self.len_all_result], batch_origin_h[i], batch_origin_w[i]
            )
            result_boxes = result_boxes.tolist()
            result_scores = result_scores.tolist()
            result_classid = result_classid.tolist()

            frame_boxes = []
            probs = []
            predictions = []
            cnt = 0
            size = 0
            for j in range(len(result_boxes)):
                box = result_boxes[j]
                box_class = self.categories[int(result_classid[j])]
                score = result_scores[j]
                if box_class in self.target_categories:
                    prediction = {'bbox': box, 'prob': score, 'class': 1}
                    predictions.append(prediction)
                    frame_boxes.append(box)
                    probs.append(score)
                    cnt += 1
                    size += ((box[2] - box[0]) * (box[3] - box[1])) / (self.input_h * self.input_w)
            output_ctx['result'].append(predictions)
            output_ctx['probs'].append(probs)
            output_ctx['parameters']['obj_num'] = cnt
            output_ctx['parameters']['obj_size'] = size / cnt if cnt != 0 else 0
        return output_ctx

    def __call__(self, images):

        assert type(images) is list
        return self.infer(images)


def calculate_iou(boxA, boxB):
    # Determine the coordinates of the intersection rectangle
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    # Compute the area of intersection
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)

    # Compute the area of both the prediction and ground-truth rectangles
    boxAArea = (boxA[2] - boxA[0] + 1) * (boxA[3] - boxA[1] + 1)
    boxBArea = (boxB[2] - boxB[0] + 1) * (boxB[3] - boxB[1] + 1)

    # Compute the intersection over union
    iou = interArea / float(boxAArea + boxBArea - interArea)

    return iou


def compute_ap(recalls, precisions):
    # Compute AP by numerical integration of the precision-recall curve
    recalls = np.concatenate(([0.0], recalls, [1.0]))
    precisions = np.concatenate(([0.0], precisions, [0.0]))
    for i in range(precisions.size - 1, 0, -1):
        precisions[i - 1] = np.maximum(precisions[i - 1], precisions[i])
    indices = np.where(recalls[1:] != recalls[:-1])[0] + 1
    ap = np.sum((recalls[indices] - recalls[indices - 1]) * precisions[indices])
    return ap


def calculate_map(predictions, ground_truths, iou_threshold=0.5):
    """
    predictions: list of dicts with keys {'bbox': [x1, y1, x2, y2], 'prob': confidence, 'class': class_id}
    ground_truths: list of dicts with keys {'bbox': [x1, y1, x2, y2], 'class': class_id}
    """
    aps = []
    for class_id in set([gt['class'] for gt in ground_truths]):
        # Filter predictions and ground truths by class
        preds = [p for p in predictions if p['class'] == class_id]
        gts = [gt for gt in ground_truths if gt['class'] == class_id]

        # Sort predictions by confidence
        preds.sort(key=lambda x: x['prob'], reverse=True)

        tp = np.zeros(len(preds))
        fp = np.zeros(len(preds))
        used_gts = set()

        for i, pred in enumerate(preds):
            max_iou = 0
            max_gt_idx = -1
            for j, gt in enumerate(gts):
                iou = calculate_iou(pred['bbox'], gt['bbox'])
                if iou > max_iou and j not in used_gts:
                    max_iou = iou
                    max_gt_idx = j

            if max_iou >= iou_threshold:
                tp[i] = 1
                used_gts.add(max_gt_idx)
            else:
                fp[i] = 1

        # Calculate precision and recall
        fp_cumsum = np.cumsum(fp)
        tp_cumsum = np.cumsum(tp)
        recalls = tp_cumsum / len(gts)
        precisions = tp_cumsum / (tp_cumsum + fp_cumsum)

        ap = compute_ap(recalls, precisions)
        aps.append(ap)

    # Mean AP
    mAP = np.mean(aps)
    return mAP


def warm_up(model, base_dir, gt_path, warm_number):
    with open(gt_path, 'r') as gt_f_:
        gt_ = gt_f_.readlines()
    count = 0
    for i_ in gt_:
        count += 1
        if count >= warm_number:
            break
        info_ = i_.split(' ')
        pic_path_ = os.path.join(base_dir, info_[0])
        frame_ = cv2.imread(pic_path_)
        model([frame_])


if __name__ == '__main__':

    resolution_dict = {'1080p': (1920, 1080),
                       '720p': (1280, 720),
                       '480p': (640, 480),
                       '360p': (640, 360)}

    video_dir = '/data/edge_computing_dataset/UA-DETRAC/Insight-MVT_Annotation_Train'
    model_dir = '../batch_test'
    batch = 1
    save_file = 'resolution_acc_delay.log'

    gt_file = '/data/edge_computing_dataset/UA-DETRAC/train_gt.txt'

    gap_cnt = 5

    if os.path.exists(save_file):
        os.remove(save_file)

    args = {
        'weights': os.path.join(model_dir, f'yolov5s_batch{batch}.engine'),
        'plugin_library': os.path.join(model_dir, f'libbatch{batch}plugins.so'),
        'batch_size': batch,
        'device': 0
    }

    estimator = CarDetection(args)

    warm_up(estimator,video_dir,gt_file, 100)

    with open(gt_file, 'r') as gt_f:
        gt = gt_f.readlines()

    avg_time = []
    avg_acc = []

    all_time_dict = {}

    for resolution in resolution_dict:

        time_buffer = []
        acc_buffer = []

        print('############################################')
        print(f'testing for resolution {resolution}..')

        cnt = 0
        for i in tqdm(gt):
            if cnt % gap_cnt != 0:
                cnt += 1
                continue

            info = i.split(' ')
            pic_path = os.path.join(video_dir, info[0])
            frame = cv2.imread(pic_path)
            frame = cv2.resize(frame, resolution_dict[resolution])

            start_time = time.time()
            result = estimator([frame])['result'][0]
            end_time = time.time()

            process_time = (end_time - start_time) * 1000
            time_buffer.append(process_time)

            bbox_gt = [float(b) for b in info[1:]]
            boxes_gt = np.array(bbox_gt, dtype=np.float32).reshape(-1, 4)
            frame_gt = []
            for box in boxes_gt.tolist():
                frame_gt.append({'bbox': box, 'class': 1})

            acc = calculate_map(result, frame_gt)
            acc_buffer.append(acc)

            # print(f'{resolution=}    acc:{acc:.2f}    delay:{process_time:.2f}ms')
            cnt += 1

        all_time_dict[resolution] = time_buffer
        avg_time.append(np.mean(time_buffer))
        avg_acc.append(np.mean(acc_buffer))

    print('******************************************')
    print('*************final result*****************')
    for resolution, frame_time, frame_acc in zip(resolution_dict, avg_time, avg_acc):
        print(f'resolution:{resolution}  time:{frame_time:.2f}ms   acc: {frame_acc:.2f}')
    print('******************************************')
    print('******************************************')

    with open(save_file, 'w') as f:
        json.dump(all_time_dict, f)

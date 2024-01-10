## 基于yolov5的目标检测接口

### 创建CarDetection类

```python
detector = CarDetection(args)
```

其中args是一个字典，包含了yolov5的可选参数，该字典是optional的，默认采用yolov5s模型，在cpu上运行，常用的可选参数如下：

```python
args = {
    weights: 'yolov5s.pt', # 模型权重文件
    device: 'cpu', # 运行设备
    conf_thres: 0.25, # 置信度阈值
    iou_thres: 0.45, # iou阈值
    img_size: 640, # 图片尺寸
    max_det: 1000, # 最大检测数    
    ... # 其他参数
}
```

在client端，可以通过如下方式创建CarDetection类：

```python client.py 
from car_detection.car_detection import CarDetection
import cv2

args = {
        'weights': 'yolov5s.pt',
        'device': 'cpu'
        # 'device': 'cuda:0'
    }

detector = CarDetection(args)
video_cap = cv2.VideoCapture(0)

while True:
    ret, frame = video_cap.read()

    input_ctx = dict()
    input_ctx['image'] = frame
    detection_reusult = detector(input_ctx)
    print('detect one frame')
```

其中input_ctx为输入的上下文，包含待检测的帧，detection_result为检测结果，检测结果为一个字典，包含了检测到的所有目标的信息，如下：

```python
detection_result = {
    'image': image, # 检测结果图片
    'result': dets, # 一个包含了所有检测结果的list，每个检测结果包含了一个检测框的坐标、置信度、类别
}
```

目录结构如下：

```bash
client.py
car_detection
├── car_detection.py
├── ...
```
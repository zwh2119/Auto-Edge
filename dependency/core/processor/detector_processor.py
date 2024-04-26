import numpy as np
from typing import List

from .processor import Processor


class DetectorProcessor(Processor):
    def __init__(self):
        super().__init__()

    def __call__(self, images: List[np.ndarray]):
        raise NotImplementedError

    def function(self):
        frame_boxes = []
        probs = []
        cnt = 0
        size = 0
        # for j in range(len(result_boxes)):
        #     box = [int(x) for x in result_boxes[j]]
        #     box_class = self.categories[int(result_classid[j])]
        #     score = result_scores[j]
        #     if box_class in self.target_categories:
        #         frame_boxes.append(box)
        #         probs.append(score)
        #         cnt += 1
        #         size += ((box[2] - box[0]) * (box[3] - box[1])) / (self.input_h * self.input_w)
        # output_ctx['result'].append(frame_boxes)
        # output_ctx['probs'].append(probs)
        # output_ctx['parameters']['obj_num'].append(cnt)
        # output_ctx['parameters']['obj_size'].append(size / cnt if cnt != 0 else 0)

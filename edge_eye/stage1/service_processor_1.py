import time

import util_ixpe
from utils import encode_image, decode_image
from log import LOGGER


class ServiceProcessor1:
    def __init__(self):
        self.d_area = [[440, 370], [790, 500]]
        self.bar_area = [[80, 390], [1130, 440], [80, 440], [1130, 490]]
        self.mat_detector = util_ixpe.MaterialDetection(
            detection_area=self.d_area, buffer_size=20)
        self.bar_selector = util_ixpe.BarSelection(bar_area=self.bar_area)
        self.first_done_flag = False

    def __call__(self, input_ctx):

        start = time.time()

        frame = input_ctx['frame']
        frame = decode_image(frame)

        end_pre = time.time()
        LOGGER.debug(f'preprocess time: {end_pre - start}s')

        output_ctx = self.process_frame(frame)

        end_process = time.time()
        LOGGER.debug(f'process time: {end_process - end_pre}s')

        if 'frame' in output_ctx:
            output_ctx['frame'] = encode_image(output_ctx['frame'])
        if 'bar_roi' in output_ctx:
            output_ctx['bar_roi'] = encode_image(output_ctx['bar_roi'])
        if 'abs_point' in output_ctx:
            output_ctx['abs_point'] = list(output_ctx['abs_point'])

        end_after = time.time()
        LOGGER.debug(f'after process time: {end_after - end_process}s')

        end = time.time()
        LOGGER.debug(f'real service call time: {end - start}s')

        return output_ctx

    def process_frame(self, frame):
        output_ctx = {}
        if not self.mat_detector.detect(frame=frame):
            LOGGER.debug('no material detected, continue')
            return output_ctx
        bar_roi, abs_point = self.bar_selector.select(frame=frame)
        if abs_point != (0, 0):
            if not self.first_done_flag:
                self.first_done_flag = True
                LOGGER.debug('select bar roi success')
            output_ctx["bar_roi"] = bar_roi
            output_ctx["abs_point"] = abs_point
            output_ctx["frame"] = frame
        return output_ctx

import cv2

from generator import Generator

from core.lib.common import ClassType, ClassFactory
from core.lib.common import LOGGER


@ClassFactory.register(ClassType.GENERATOR, alias='video')
class VideoGenerator(Generator):
    def __init__(self, source_id: int, task_pipeline: list,
                 data_source: str, metadata: dict):
        super().__init__(source_id, task_pipeline, metadata)

        self.task_id = 0
        self.video_data_source = data_source
        self.data_source_capture = None
        self.frame_buffer = []

        self.frame_filter = None

    def get_one_frame(self):
        if self.data_source_capture:
            self.data_source_capture = cv2.VideoCapture(self.video_data_source)

        ret, frame = self.data_source_capture.read()
        first_no_signal = True

        # retry when no video signal
        while not ret:
            if first_no_signal:
                LOGGER.warning(f'No video signal from source {self.generator_id}!')
                first_no_signal = False
            self.data_source_capture = cv2.VideoCapture(self.video_data_source)
            ret, frame = self.data_source_capture.read()

        if not first_no_signal:
            LOGGER.warning(f'Get video stream data from source {self.generator_id}..')

        return frame

    def compress_frames(self):
        assert type(self.frame_buffer) is list and len(self.frame_buffer) > 0, 'Frame buffer is empty'

    def run(self):
        self.frame_buffer = []
        while True:
            frame = self.get_one_frame()
            if self.frame_filter(self.frame_buffer, frame):
                self.frame_buffer.append(frame)
            if len(self.frame_buffer) >= self.meta_data['buffer_size']:
                self.compress_frames()

import cv2

from generator import Generator

from lib.common import ClassType, ClassFactory
from lib.common import LOGGER
from lib.common import Context


@ClassFactory.register(ClassType.GENERATOR, alias='video')
class VideoGenerator(Generator):
    def __init__(self, source_id: int, task_pipeline: list,
                 data_source: str, metadata: dict):
        super().__init__(source_id, task_pipeline, metadata)

        self.task_id = 0
        self.video_data_source = data_source
        self.data_source_capture = None
        self.frame_buffer = []

        self.frame_filter = Context.get_algorithm('GEN_FILTER')
        self.frame_process = Context.get_algorithm('GEN_PROCESS')
        self.frame_compress = Context.get_algorithm('GEN_COMPRESS')

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

    def filter_frame(self, frame):
        assert type(self.frame_buffer) is list, 'Frame buffer is not list'

    def process_frame(self, frame):
        pass

    def compress_frames(self):
        assert type(self.frame_buffer) is list and len(self.frame_buffer) > 0, 'Frame buffer is not list or is empty'

    def run(self):
        self.frame_buffer = []
        while True:
            self.request_schedule_policy()

            frame = self.get_one_frame()
            if self.filter_frame(frame):
                self.process_frame(frame)
                self.frame_buffer.append(frame)
            if len(self.frame_buffer) >= self.meta_data['buffer_size']:
                self.compress_frames()

                self.submit_task_to_controller()

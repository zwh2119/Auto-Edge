import threading

import cv2

from .generator import Generator
from core.lib.content import Task

from core.lib.common import ClassType, ClassFactory
from core.lib.common import LOGGER
from core.lib.common import Context
from core.lib.common import FileOps


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
        if not self.data_source_capture:
            self.data_source_capture = cv2.VideoCapture(self.video_data_source)

        ret, frame = self.data_source_capture.read()
        first_no_signal = True

        # retry when no video signal
        while not ret:
            if first_no_signal:
                LOGGER.warning(f'No video signal from source {self.source_id}!')
                first_no_signal = False
            self.frame_buffer = []
            self.data_source_capture = cv2.VideoCapture(self.video_data_source)
            ret, frame = self.data_source_capture.read()

        if not first_no_signal:
            LOGGER.info(f'Get video stream data from source {self.source_id}..')

        return frame

    def filter_frame(self, frame):
        assert type(self.frame_buffer) is list, 'Frame buffer is not list'
        return self.frame_filter(self, frame)

    def process_frame(self, frame):
        return self.frame_process(self, frame)

    def compress_frames(self, frame_buffer):
        assert type(frame_buffer) is list and len(frame_buffer) > 0, 'Frame buffer is not list or is empty'
        return self.frame_compress(self, frame_buffer)

    def submit_task_to_controller(self, compressed_path):
        self.current_task = Task(source_id=self.source_id,
                                 task_id=self.task_id,
                                 source_device=self.local_device,
                                 pipeline=self.task_pipeline,
                                 metadata=self.meta_data,
                                 raw_metadata=self.raw_meta_data,
                                 content=self.task_content,
                                 file_path=compressed_path
                                 )
        self.record_total_start_ts()
        super().submit_task_to_controller(compressed_path)

    def process_full_frame_buffer(self, frame_buffer):

        LOGGER.debug(f'[Frame Buffer] buffer size: {len(frame_buffer)}')

        frame_buffer = [self.process_frame(frame) for frame in frame_buffer]

        self.request_schedule_policy()

        self.task_id += 1
        compressed_file_path = self.compress_frames(frame_buffer)

        self.submit_task_to_controller(compressed_file_path)

        FileOps.remove_file(compressed_file_path)

    def run(self):
        self.frame_buffer = []

        # initialize default schedule policy
        self.after_schedule_operation(self, None)

        while True:

            frame = self.get_one_frame()
            if self.filter_frame(frame):
                self.frame_buffer.append(frame)

            if len(self.frame_buffer) >= self.meta_data['buffer_size']:
                threading.Thread(target=self.process_full_frame_buffer, args=(self.frame_buffer.copy(),)).start()
                self.frame_buffer = []

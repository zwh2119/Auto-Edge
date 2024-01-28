import util_ixpe

class ServiceProcessor1:
    def __init__(self):
        self.d_area = [[440, 370], [790, 500]]
        self.bar_area = [[80, 390], [1130, 440], [80, 440], [1130, 490]]
        self.mat_detector = util_ixpe.MaterialDetection(
            detection_area=self.d_area, buffer_size=20)
        self.bar_selector = util_ixpe.BarSelection(bar_area=self.bar_area)
        self.first_done_flag = False

    def __call__(self, data):
        pass

    def process_frame(self, frame):
        output_ctx = {}
        if not self.mat_detector.detect(frame=frame):
            print('no material detected, continue')
            return output_ctx
        bar_roi, abs_point = self.bar_selector.select(frame=frame)
        if abs_point != (0, 0):
            if not self.first_done_flag:
                self.first_done_flag = True
                print('select bar roi success')
            output_ctx["bar_roi"] = bar_roi
            output_ctx["abs_point"] = abs_point
            output_ctx["frame"] = frame
        return output_ctx

import util_ixpe

class ServiceProcessor3:
    def __init__(self, cfg):
        self.lps = 0
        self.rps = 0
        self.pos_calculator = util_ixpe.CalPosition()
        self.abnormal_detector = util_ixpe.AbnormalDetector(
            w1=5, w2=7, e=7, buffer_size=100)
        self.lastls = self.lps
        self.lastrs = self.rps
        self.first_done_flag = False
        self.frame = None

    def __call__(self, data, metadata):
        pass

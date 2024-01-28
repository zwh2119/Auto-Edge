import util_ixpe

class ServiceProcessor3:
    def __init__(self):
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

    def process_task(self, input_ctx):
        output_ctx = {}
        if 'frame' not in input_ctx:
            # return empty due to no input_ctx
            return output_ctx
        if len(input_ctx) == 3:
            print("get three parameters from input_ctx")
            bar_roi, abs_point, self.frame = input_ctx["bar_roi"], input_ctx["abs_point"], input_ctx["frame"]
            self.lps, self.rps = self.pos_calculator.calculatePosInBarROI(
                bar_roi=bar_roi, abs_point=abs_point)

            if self.lps != 0:
                self.lastls = self.lps
            else:
                self.lps = self.lastls
            if self.lps != 0:
                self.lps = int(self.lps + abs_point[0])

            if self.rps != 0:
                self.lastrs = self.rps
            else:
                self.rps = self.lastrs
            if self.rps != 0:
                self.rps = int(self.rps + abs_point[0])

        elif len(input_ctx) == 5:
            print("get five parameters from input_ctx")
            if not self.first_done_flag:
                self.first_done_flag = True
                print('start get SR frame from queue')
            # 因为roi size变大 2*h and 2*w 导致不能直接使用计算出来的单位xxx
            lroi, rroi, labs_point, rabs_point, self.frame = input_ctx["srl"], input_ctx["srr"], input_ctx[
                "labs_point"], input_ctx["rabs_point"], input_ctx["frame"]
            # print(type(lroi))
            # print(type(rroi))
            print(labs_point)
            print(rabs_point)
            if len(lroi) == 1:
                self.lps = lroi
            else:
                self.lps = self.pos_calculator.calculatePosInMROI(
                    lroi, 'left', labs_point)  # func 2
                self.lps = int(self.lps + labs_point[0])
            if len(rroi) == 1:
                self.rps = rroi
            else:
                self.rps = self.pos_calculator.calculatePosInMROI(
                    rroi, 'right', rabs_point)
                self.rps = int(self.rps + rabs_point[0])

        # calculate edge positions
        # lps, rps = abnormal_detector.repair(lpx=lps, rpx=rps)  # func3
        # update lps, rps
        self.set_edge_position(int(self.lps), int(self.rps))
        output_ctx["frame"] = self.frame
        output_ctx["lps"] = self.lps
        output_ctx["rps"] = self.rps
        return output_ctx

    def set_edge_position(self, lps, rps):
        pass

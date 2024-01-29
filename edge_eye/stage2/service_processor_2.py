import util_ixpe
from client import http_request
from utils import encode_image, decode_image


class ServiceProcessor2:
    def __init__(self, cfg):
        model_path = cfg['model_path']
        self.sr_generator = util_ixpe.ESCPN(model_path)

    def __call__(self, input_task, redis_address):
        output = []
        for input_ctx in input_task:

            if 'bar_roi' in input_ctx:
                input_ctx['bar_roi'] = decode_image(input_ctx['bar_roi'])
            if 'abs_point' in input_ctx:
                input_ctx['abs_point'] = tuple(input_ctx['abs_point'])

            output_ctx = self.process_task(input_ctx, redis_address)

            if 'bar_roi' in output_ctx:
                output_ctx['bar_roi'] = encode_image(output_ctx['bar_roi'])
            if "abs_point" in output_ctx:
                output_ctx["abs_point"] = list(output_ctx["abs_point"])
            if "srl" in output_ctx:
                output_ctx["srl"] = encode_image(output_ctx["srl"])
            if "srr" in output_ctx:
                output_ctx["srr"] = encode_image(output_ctx["srr"])
            if "labs_point" in output_ctx:
                output_ctx["labs_point"] = list(output_ctx["labs_point"])
            if "rabs_point" in output_ctx:
                output_ctx["rabs_point"] = list(output_ctx["rabs_point"])

            output.append(output_ctx)
        return output

    def process_task(self, input_ctx, redis_address):
        output_ctx = {}

        bar_roi, abs_point = input_ctx["bar_roi"], input_ctx["abs_point"]
        abs_point = tuple(abs_point)
        lps, rps = self.get_edge_position(redis_address)
        print(f"lps: {lps}, rps: {rps}")

        if lps == 0 and rps == 0:
            output_ctx["bar_roi"] = bar_roi
            output_ctx["abs_point"] = abs_point

            # case 2: return 3 parameters
            # print("case 2: return 3 parameters")
            return output_ctx
        else:
            lroi, rroi, p1, p3 = self.extractMinimizedROI(
                bar_roi, lps, rps, abs_point)
            if lroi.size == 0 or rroi.size == 0:
                # case 3: return empty
                # print("case 3: return empty")
                return output_ctx
            else:
                srl = self.sr_generator.genSR(lroi)
                srr = self.sr_generator.genSR(rroi)

                labs_point = (abs_point[0] + p1[0], abs_point[1] + p1[1])
                rabs_point = (abs_point[0] + p3[0], abs_point[1] + p3[1])
                output_ctx["srl"] = srl
                output_ctx["srr"] = srr
                output_ctx["labs_point"] = labs_point
                output_ctx["rabs_point"] = rabs_point

                # case 4: return 5 parameters
                # print("case 4: return 5 parameters")
                return output_ctx

    def extractMinimizedROI(self, bar_roi, lps, rps, abs_point):
        lps = int(lps - abs_point[0])
        rps = int(rps - abs_point[0])
        sliding_threshold = 10
        hl_threshold = 15
        height = bar_roi.shape[0]
        p1 = (lps - 3 * hl_threshold - sliding_threshold, 0)
        p2 = (lps + hl_threshold + sliding_threshold, height)
        p3 = (rps - hl_threshold - sliding_threshold, 0)
        p4 = (rps + 3 * hl_threshold + sliding_threshold, height)
        lroi = bar_roi[p1[1]:p2[1], p1[0]:p2[0]]
        rroi = bar_roi[p3[1]:p4[1], p3[0]:p4[0]]
        return lroi, rroi, p1, p3

    def get_edge_position(self, redis_address):
        response = http_request(url=redis_address, method='GET')
        if response:
            return response['lps'], response['rps']
        else:
            return 0, 0

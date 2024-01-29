
from scipy.optimize import leastsq
import threading

from scipy import stats


import numpy as np
import torch
from PIL import Image
from torch.autograd import Variable
from torchvision.transforms import ToTensor



from model import Net

import time

import cv2 as cv


is_show_frame = True

def is_image_file(filename):
    return any(filename.endswith(extension) for extension in ['.png', '.jpg', '.jpeg', '.JPG', '.JPEG', '.PNG'])


def is_video_file(filename):
    return any(filename.endswith(extension) for extension in ['.mp4', '.avi', '.mpg', '.mkv', '.wmv', '.flv'])



def showFrame(frame: list, window_name: str) -> None:
    """show the frame with given window_name"""
    if is_show_frame:
        try:
            cv.imshow(window_name, frame)
            cv.waitKey(1)
        except Exception as e:
            print('error on show frame %s' % window_name, str(e), frame.shape)


def perspectiveTransformation(img_src):
    height, width = img_src.shape[:2]
    # 2.创建原图与目标图的对应点
    src_point = np.float32([[width * 0.15, 0], [width - 1, 0],
                            [0, height - 1], [width * 0.85, height - 1]])

    dst_point = np.float32([[0, 0], [width - 1, 0],
                            [0, height - 1], [width - 1, height - 1]])
    perspective_matrix = cv.getPerspectiveTransform(src_point, dst_point)
    # 4.执行透视变换
    img_dst = cv.warpPerspective(img_src, perspective_matrix, (width, height))
    return img_dst


def imgEntropy(image):
    if image.ndim > 2:
        image = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    simplified_image = image // 16  # (0,255) - (0,16)
    prob = np.bincount(np.reshape(simplified_image, -1))
    entropy = stats.entropy(prob)
    return entropy


def sobel_xaxis(img):
    img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    img_sobel_x = cv.Sobel(img, cv.CV_64F, 1, 0, ksize=3)
    img_sobel_x = cv.convertScaleAbs(img_sobel_x)
    return img_sobel_x


def edgeDetection(frame, accuray='normal', operator='canny', ff=None):
    if ff is None:
        ff = {
            'ksize': (3, 3),
            'sigmaX': 0,
            'lThreshold': 50,
            'hThreshold': 150,
            'vl': 30,
            'hl': 30,
            'theta': 0.436,
            'apertureSize': 3,
            'L2gradient': False
        }
        if accuray == 'low':
            ff['lThreshold'] = 70
            ff['hThreshold'] = 210
            ff['apertureSize'] = 5
        elif accuray == 'high':
            ff['lThreshold'] = 20
            ff['hThreshold'] = 60
            ff['apertureSize'] = 7
            ff['L2gradient'] = True
    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
    # grayGaussian = gray
    grayGaussian = cv.GaussianBlur(gray, ff['ksize'], ff['sigmaX'])
    if operator == 'canny':
        edges = cv.Canny(grayGaussian, ff['lThreshold'], ff['hThreshold'],
                         apertureSize=ff['apertureSize'], L2gradient=ff['L2gradient'])
    elif operator == 'sobel':
        img_sobel_x = cv.Sobel(grayGaussian, cv.CV_64F, 1, 0, ksize=3)
        img_sobel_y = cv.Sobel(grayGaussian, cv.CV_64F, 0, 1, ksize=3)
        img_sobel_x = cv.convertScaleAbs(img_sobel_x)
        img_sobel_y = cv.convertScaleAbs(img_sobel_y)
        edges = cv.addWeighted(img_sobel_x, 0.5, img_sobel_y, 0.5, 0)
    elif operator == 'laplace':
        gray_lap = cv.Laplacian(grayGaussian, cv.CV_16S, ksize=3)
        edges = cv.convertScaleAbs(gray_lap)
    elif operator == 'scharr':
        img_scharr_x = cv.Scharr(grayGaussian, cv.CV_64F, 1, 0)
        img_scharr_y = cv.Scharr(grayGaussian, cv.CV_64F, 0, 1)
        img_scharr_x = cv.convertScaleAbs(img_scharr_x)
        img_scharr_y = cv.convertScaleAbs(img_scharr_y)
        edges = cv.addWeighted(img_scharr_x, 0.5, img_scharr_y, 0.5, 0)
    # lines = cv.HoughLines(edges, 1, np.pi/180, 25)
    # lines1 = cv.HoughLines(
    #     edges, 1, np.pi/180, ff.hl_threshold, min_theta=0, max_theta=ff.t_threshold)  # 考虑更换为概率霍夫变换？？
    # lines2 = cv.HoughLines(edges, 1, np.pi/180, ff.hl_threshold,
    #                         min_theta=(np.pi-ff.t_threshold), max_theta=np.pi)
    return edges


# dp03, 21.7.8-20:35-xxx 这一个小时的raw视频记得拿出来
# 比较有意义


class MaterialDetection:
    def __init__(self, detection_area, buffer_size) -> None:
        self.p1, self.p2 = detection_area
        self.buffer_size = buffer_size
        shape = (720, 1280, 3)
        raw_background = cv.imread('images/Empty_background.png')
        self.background = raw_background[self.p1[1]:self.p2[1], self.p1[0]:self.p2[0]]
        # 记得初始化这个玩意
        self.counter = 0
        self.threshold_update = 0.05
        self.threshold_material = 1.0
        self.isMaterial = False

    def detect(self, frame):
        """奇妙的counter状态机xxx，节省资源，false时每一帧都比对，true时跳帧比对，以及background动态更新"""
        if self.isMaterial:
            self.counter += 1
            if self.counter <= 10:
                return self.isMaterial
            else:
                self.counter = 0
        d_area = frame[self.p1[1]:self.p2[1], self.p1[0]:self.p2[0]]
        if len(self.background) == 0:
            self.background = d_area
            self.counter = 0
        else:
            self.counter += 1
            diff_img = cv.absdiff(self.background, d_area)
            entropy = imgEntropy(diff_img)
            if entropy > self.threshold_material:
                self.isMaterial = True
                self.counter = 0
            else:
                self.isMaterial = False
                if entropy < self.threshold_update and self.counter > 60:
                    self.background = d_area
                    self.counter = 0
        return self.isMaterial


class BarSelection:
    def __init__(self, bar_area, buffer_size=10) -> None:
        self.p1, self.p2, self.p3, self.p4 = bar_area  # p1,p2,p3,p4 的实际位置以及数据有点怪，仔细看看xx
        self.abs_point = (0, 0)
        self.buffer_size = buffer_size
        self.top_value = []
        self.bottom_value = []

    def calScore(self, frame):
        height, width = frame.shape[:2]
        step = 5
        myList = [[0, 0, 0]] * (width // step)
        # TODO:为什么这里滑动窗口只扫描了前面的一部分（0~(width // step - 1) + step * 10）？width可是有1050呢。
        for i in range(0, width // step):
            sw = frame[:, i:i + step * 10]  # sw: sliding window
            line = np.max(sw, axis=1)  # TODO:这里是假设滑动窗口里只会出现竖直边缘那一条线吗？应该是
            myList[i] = [i, np.mean(line), np.std(line)]
        myList = np.array(myList)
        index1 = myList[:, 1].argmax()
        _, mu1, sigma1 = myList[index1]
        le_bound = max(0, index1 - step * 10)
        ri_bound = min(index1 + step * 10, width - 1)
        myList[le_bound:ri_bound] = [index1, 0, 0]
        index2 = myList[:, 1].argmax()
        _, mu2, sigma2 = myList[index2]
        score = mu1 + mu2 - abs(mu1 - mu2) - np.log((sigma1 + 1) * (sigma2 + 1))
        return score

    def select(self, frame):
        roi1 = frame[self.p1[1]:self.p2[1], self.p1[0]:self.p2[0]]
        roi2 = frame[self.p3[1]:self.p4[1], self.p3[0]:self.p4[0]]
        if self.abs_point == (0, 0):
            if len(self.top_value) < self.buffer_size and len(self.bottom_value) < self.buffer_size:
                # TODO：这里的top和bottom是指bar的位置关系
                top_edges = sobel_xaxis(roi1)
                bottom_edges = sobel_xaxis(roi2)
                self.top_value.append(self.calScore(top_edges))
                self.bottom_value.append(self.calScore(bottom_edges))
            if len(self.top_value) >= self.buffer_size and len(self.bottom_value) >= self.buffer_size:
                s1 = np.mean(self.top_value)
                s2 = np.mean(self.bottom_value)
                if s1 >= s2:
                    self.abs_point = self.p1
                else:
                    self.abs_point = self.p3
        if self.abs_point == self.p1:
            return roi1, self.abs_point
        elif self.abs_point == self.p3:
            return roi2, self.abs_point
        else:
            return frame, self.abs_point


class CachePool:
    def __init__(self, buffer_size=10) -> None:
        self.lpool = [[], [], []]  # frame, result, time
        self.rpool = [[], [], []]
        self.buffer_size = buffer_size
        self.lpos = 0
        self.rpos = 0
        self.llock = threading.Lock()
        self.rlock = threading.Lock()
        self.hit_threshold = 0.05
        self.initPool(self.lpool, self.buffer_size)
        self.initPool(self.rpool, self.buffer_size)

    def initPool(self, pool, buffer_size):
        while len(pool[0]) < buffer_size:
            fs, rs, ts = pool
            fs.append(np.empty(shape=(100, 160, 3)))
            rs.append(-1)
            ts.append(time.time())

    def hit(self, location, frame):  # 考虑这个hit操作xxx
        lock = self.llock
        pool = self.lpool
        result = -1
        if location == 'r':
            lock = self.rlock
            pool = self.rpool
        lock.acquire()
        if len(pool) < self.buffer_size:
            pass  # do nothing
        else:
            score_recorder = []
            fs, rs, ts = pool
            for c_frame, c_result, c_time in zip(fs, rs, ts):
                score = self.calDiffScore(frame, c_frame)
                score_recorder.append(score)
            cache_index = np.argmin(score_recorder)
            cache_score = score_recorder[cache_index]
            if cache_score < self.hit_threshold:
                result = pool[1][cache_index]
                pool[2][cache_index] = time.time()
        lock.release()
        return result

    def update(self, location, frame=None, result=None):
        # only update for mroi !!
        lock = self.llock
        pool = self.lpool
        if location == 'r':
            lock = self.rlock
            pool = self.rpool
        lock.acquire()

        p_index = len(pool[0])
        if p_index >= self.buffer_size:
            c_times = pool[-1]
            p_index = np.argmin(c_times)
        if frame is not None:
            # list assignment index out of range ！ need to update !
            pool[0][p_index] = frame

        if result is not None:
            pool[1][p_index] = result
            pool[-1][p_index] = time.time()

        lock.release()

    def calDiffScore(self, f1, f2):
        score = 0
        diff_frame = cv.absdiff(f1, f2)
        score = imgEntropy(diff_frame)
        return score


class ESCPN:
    def __init__(self, model_path) -> None:
        model = Net(upscale_factor=2)
        model.load_state_dict(torch.load(
            model_path, map_location=torch.device('cpu')))
        self.model = model

    def genSR(self, frame):
        model = self.model
        if frame.size == 0:
            return frame
        img = Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2YCrCb))
        y, cb, cr = img.split()
        image = Variable(ToTensor()(y)).view(1, -1, y.size[1], y.size[0])
        out = model(image)
        out = out.cpu()
        out_img_y = out.data[0].numpy()
        out_img_y *= 255.0
        out_img_y = out_img_y.clip(0, 255)
        out_img_y = Image.fromarray(np.uint8(out_img_y[0]), mode='L')
        out_img_cb = cb.resize(out_img_y.size, Image.BICUBIC)
        out_img_cr = cr.resize(out_img_y.size, Image.BICUBIC)
        out_img = Image.merge(
            'YCbCr', [out_img_y, out_img_cb, out_img_cr])
        sr_img = cv.cvtColor(np.asarray(out_img), cv.COLOR_YCrCb2BGR)
        return sr_img


class CalPosition:
    def __init__(self) -> None:
        self.ff = {
            'initial': False,
            'ksize': (3, 3),
            'sigmaX': 0,
            'lThreshold': 60,
            'hThreshold': 150,
            'vl': 30,
            'hl': 30,
            'theta': 0.436,
            'apertureSize': 3,
            'L2gradient': False
        }
        self.commom_points = []
        self.sta_points = []
        self.mov_points = []
        self.extract_counter = 0
        # 先把阈值的数值设定搞完。。。

        self.vertical_threshold = {'rho': 25, 'theta': np.pi / 180 * 30}  # 360: 0-30, 150-180
        self.horizontal_threshold = {'rho': 25, 'theta': np.pi / 180 * 15}  # 360: 75-105
        self.le_last = 0
        self.ri_last = 0
        self.centerLine = 30
        self.abs_point = (0, 0)

    def extractCommomPoints(self, edges):
        if self.extract_counter == 0:
            self.commom_points = edges
        elif self.extract_counter < 20:
            self.commom_points &= edges
        else:
            if self.extract_counter > 100:  # 随便操作下防止溢出
                self.extract_counter = 19
        self.extract_counter += 1
        return self.extract_counter

    def generateDoubleThreshold(self, frame):
        if self.ff['initial']:
            pass
        else:
            performance = False
            while True:
                lThreshold = self.ff['lThreshold']
                hThreshold = self.ff['hThreshold']

                if frame is None:
                    raise ValueError("frame is None")
                if frame.size == 0:
                    raise ValueError("frame is empty")
                if frame.dtype not in [np.uint8, np.uint16, np.float32]:
                    raise ValueError(f"frame has an invalid data type: {frame.dtype}")

                gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
                edges = cv.Canny(gray, lThreshold, hThreshold)
                # this performance is really important !!
                # vertical boundary and horizontal reference bar should all in consideration !!
                performance = self.evaPerformance(edges)
                if performance:
                    self.ff['initial'] = performance
                    lThreshold = self.ff['lThreshold']
                    hThreshold = self.ff['hThreshold']
                    break
                else:
                    if lThreshold >= 35:
                        lThreshold -= 10
                    if hThreshold >= 105:
                        hThreshold -= 20
        return self.ff

    # 有机会的话 把各处的图像都imshow出来，方便操作xxx观察下到底是哪一步出了问题xx
    def evaPerformance(self, edges):
        vPerformance = False
        hPerformance = False
        vl = self.ff['vl']
        lines = cv.HoughLines(edges, 1, np.pi / 180, vl)
        theta_threshold = np.pi / 6
        height, width = edges.shape[:2]
        boundry = width // 2
        max_material_width = width // 5 * 4
        if lines is not None:
            lLine = []
            rLine = []
            hRhoCount = []
            for line in lines:
                rho, theta = line[0]
                # horizontal line detection 75~105
                if theta >= np.pi / 180 * 75 and theta <= np.pi / 180 * 105:
                    hRhoCount.append(rho)
                # vertical line detection
                if (rho > 0 and theta < theta_threshold) or (rho < 0 and np.pi - theta < theta_threshold):
                    if abs(rho) > boundry:
                        rLine.append(abs(rho))
                    else:
                        lLine.append(abs(rho))
            if min(rLine) - max(lLine) < max_material_width:
                vPerformance = True
            hRhoCount.sort()
            topline = np.sum(1 for num in hRhoCount if num < (hRhoCount[0] + hRhoCount[-1]) / 2)
            bottomline = np.sum(1 for num in hRhoCount if num > (hRhoCount[0] + hRhoCount[-1]) / 2)
            if topline > 4 or bottomline > 4:
                hPerformance = True

        return vPerformance and hPerformance

    def calculatePosInBarROI(self, bar_roi, abs_point):
        self.abs_point = abs_point
        ff = self.generateDoubleThreshold(bar_roi)
        edges = edgeDetection(bar_roi, ff=ff)

        # showFrame(edges,'original_edges')
        counter = self.extractCommomPoints(edges)
        if counter < 20:
            return 0, 0
        self.sta_points = edges & self.commom_points
        self.mov_points = edges - self.sta_points
        # showFrame(self.commom_points,'common_points')
        # showFrame(self.sta_points,'sta_points')
        # showFrame(self.mov_points,'mov_points')
        boundry_line = self.calculateBoundry(self.mov_points)
        lsp, rsp = self.sta_points[...,
                   :boundry_line], self.sta_points[..., boundry_line + 1:]
        lmp, rmp = self.mov_points[...,
                   :boundry_line], self.mov_points[..., boundry_line + 1:]
        le, re = edges[..., :boundry_line], edges[..., boundry_line + 1:]
        lps = self.biDirectionTracking(
            le, lsp, lmp, self.commom_points[..., : boundry_line], pos='left')
        rps = self.biDirectionTracking(
            re, rsp, rmp, self.commom_points[..., boundry_line + 1:], pos='right')
        return lps, rps + boundry_line

    def calculateBoundry(self, mov_points):
        height, width = mov_points.shape[:2]
        boundry = width // 2
        # further improvement by distance separation
        return boundry

    def calculatePosInMROI(self, mroi, position='left', abs_point=(0, 0)):
        lps = 0
        rps = 0
        ff = self.ff
        # 这里的edges只是一块区域，最好附加上相对于bar_roi的详细位置
        super_edges = edgeDetection(mroi, ff=ff)
        # showFrame(super_edges, 'sr_edges_' + position)
        edges = cv.resize(super_edges, None, fx=0.5, fy=0.5, interpolation=cv.INTER_AREA)
        # showFrame(edges, 'lr_edges_' + position)
        relative_px = abs_point[0] - self.abs_point[0]
        relative_py = abs_point[1] - self.abs_point[1]
        # logger.info("relative_px = %s, relative_py = %s" % (relative_px, relative_py))
        width, height = edges.shape[:2]
        # logger.info("edge_width = %s, edge_height = %s" % (width, height))
        # logger.info("common_points_shape = (%s, %s)" % np.array(self.commom_points).shape)

        # print("relative_px = %s, relative_py = %s" % (relative_px, relative_py))
        # print("edge_width = %s, edge_height = %s" % (width, height))
        # print(self.commom_points)
        common_points = self.commom_points[relative_py:(relative_py+width), relative_px:(relative_px+height)]  # xxx
        # showFrame(common_points, 'common_points')
        # further improvement by set local points
        self.sta_points = edges & common_points
        self.mov_points = edges - self.sta_points
        # showFrame(self.sta_points, 'sta_points')
        # showFrame(self.mov_points, 'mov_points')
        # logger.info("sta_points_len = %s, mov_points_len = %s" % (len(self.sta_points), len(self.mov_points)))
        if position == 'left':
            lps = self.biDirectionTracking(
                edges, self.sta_points, self.mov_points, common_points, position)
            return lps
        elif position == 'right':
            rps = self.biDirectionTracking(
                edges, self.sta_points, self.mov_points, common_points, position)
            return rps
        else:
            return -1

    def complimentaryFilter(self, vl, hl, last):
        if vl < 0 and hl < 0:
            return last
        elif vl < 0:
            return hl
        elif hl < 0:
            return vl
        dis = abs(vl - last) + abs(hl - last)
        if dis == 0:
            return vl
        cur = abs(vl - last) * hl + abs(hl - last) * vl
        cur = cur / dis
        return cur

    def calAxisPoints(self, line, x=None, y=None):
        ''' houghlines 直线的计算需要特别注意才行，特殊的定义
        目前来看这里的计算很可能出现了点问题xxx
        '''
        rho, theta = line
        if x is not None:
            y = rho - x * np.cos(theta)
            if np.sin(theta) == 0:
                y = 0
            else:
                y = y / np.sin(theta)
            return y
        if y is not None:
            x = rho - y * np.sin(theta)
            if np.cos(theta) == 0:
                x = 0
            else:
                x = x / np.cos(theta)
            return x

    def biDirectionTracking(self, edges, sta, mov, common_points, pos='left'):  # TODO:问题在这里面
        # showFrame(edges, 'bi-edges-%s' % pos)
        lines = cv.HoughLines(
            edges, 1, np.pi / 180, self.vertical_threshold['rho'])
        vTrack = []
        if lines is not None:
            for line in lines:
                rho, theta = line[0]
                theta_threshold = self.vertical_threshold['theta']
                if (rho > 0 and theta < theta_threshold) or (rho < 0 and np.pi - theta < theta_threshold):
                    vTrack.append([rho, theta])
        vl = -1  # init value for vertical line tracking result (x value)
        if len(vTrack) > 0:
            vlRes = []
            for li in vTrack:
                vlRes.append(self.calAxisPoints(li, y=self.centerLine))
            vl = np.average(vlRes)
        hlines = cv.HoughLinesP(edges, 1, np.pi / 180, self.horizontal_threshold['rho'], minLineLength=20,
                                maxLineGap=10)
        hTrack = []
        if hlines is not None:
            for line in hlines:
                x1, y1, x2, y2 = line[0]
                if pos == 'left':
                    hTrack.append(max(x1, x2))
                else:
                    hTrack.append(min(x1, x2))
        hl = -1  # init value for horizontal line tracking result (x value)
        if len(hTrack) > 0:
            if pos == 'left':
                hl = max(hTrack)
            else:
                hl = min(hTrack)
        position = 0
        if pos == 'left':
            position = self.complimentaryFilter(vl, hl, self.le_last)   # TODO:似乎是vl和hl求得不好
            lpx_log = '%s-%s-%s' % (vl, hl, position)
            # logger1.info('lpx log : ' + lpx_log)
            self.le_last = position
        elif pos == 'right':
            position = self.complimentaryFilter(vl, hl, self.ri_last)
            rpx_log = '%s-%s-%s' % (vl, hl, position)
            # logger2.info('rpx log : ' + rpx_log)
            self.ri_last = position
        return position

    def biDirectionTracking_bak(self, edges, sta, mov, common_points, pos='left'):
        '''实际运行之中还是太敏感了/common的提取效果没有想象之中的那么好--水平追踪时，边缘点经常发生变换
        整体的edges提取效果还可以
        '''
        # showFrame(edges, 'bi-edges-%s' % pos)
        # showFrame(sta, 'bi-sta-%s' % pos)
        # showFrame(mov, 'bi-mov-%s' % pos)
        # showFrame(common_points, 'bi-common_points-%s' % pos)
        lps = 0
        rps = 0
        vTrack = []
        hTrack = []
        lines = cv.HoughLines(
            mov, 1, np.pi / 180, self.vertical_threshold['rho'])
        if lines is None:
            lines = cv.HoughLines(edges, 1, np.pi / 180,
                                  self.vertical_threshold['rho'])
        if lines is not None:
            for line in lines:
                rho, theta = line[0]
                theta_threshold = self.vertical_threshold['theta']
                if (rho > 0 and theta < theta_threshold) or (rho < 0 and np.pi - theta < theta_threshold):
                    vTrack.append([rho, theta])
        # xxx
        hlines = cv.HoughLines(
            sta, 1, np.pi / 180, self.horizontal_threshold['rho'])
        if hlines is None:
            # operands could not be broadcast together with shapes (50,1050) (50,524)
            sta = common_points - common_points & edges
        vl = -1  # init value for vertical line tracking result (x value)
        if len(vTrack) > 0:
            vlRes = []
            for li in vTrack:
                vlRes.append(self.calAxisPoints(li, y=self.centerLine))
            vl = np.average(vlRes)
        hl = -1  # init value for horizontal line tracking result (x value)
        if len(hTrack) > 0:
            # xxx
            if pos == 'left':
                hl = np.max(sta[..., 1])  # find the centerest points in lsta
            elif pos == 'right':
                hl = np.min(sta[..., 1])  # same to hl
            else:
                hl = 0
        if pos == 'left':
            position = self.complimentaryFilter(vl, hl, self.le_last)
            self.le_last = position
        elif pos == 'right':
            position = self.complimentaryFilter(vl, hl, self.ri_last)
            self.ri_last = position
        else:
            position = 0
        return position


class AbnormalDetector:
    def __init__(self, w1, w2, e, buffer_size=100) -> None:
        self.threshold_w1 = w1
        self.threshold_w2 = w2
        self.threshold_e = e
        self.le_pos = []
        self.ri_pos = []
        self.material_width = []
        self.buffer_size = 100

    def repair(self, lpx, rpx):
        width = abs(rpx - lpx)
        if len(self.material_width) <= self.buffer_size // 10:
            pass
        else:
            d_lpx = abs(lpx - self.le_pos[-1])
            d_rpx = abs(rpx - self.ri_pos[-1])
            d_width = abs(self.material_width[-1] - width)
            if d_width <= self.threshold_w1 or (d_lpx <= self.threshold_e and d_rpx <= self.threshold_e):
                pass
            elif d_lpx > 2 * self.threshold_e or d_rpx > 2 * self.threshold_e:
                if d_lpx > 2 * self.threshold_e:
                    lpx = self.threshold_e
                if d_rpx > 2 * self.threshold_e:
                    rpx = self.threshold_e
            elif self.threshold_w1 < d_width < self.threshold_w2:
                if self.threshold_e < d_lpx < 2 * self.threshold_e:
                    lpx = 0.9 * self.threshold_e + 0.1 * lpx
                if self.threshold_e < d_rpx < 2 * self.threshold_e:
                    rpx = 0.9 * self.threshold_e + 0.1 * rpx
            else:
                if self.threshold_e < d_lpx < 2 * self.threshold_e:
                    lpx = 0.99 * self.threshold_e + 0.01 * lpx
                if self.threshold_e < d_rpx < 2 * self.threshold_e:
                    rpx = 0.99 * self.threshold_e + 0.01 * rpx
        self.le_pos.append(lpx)
        self.ri_pos.append(rpx)
        self.material_width.append(width)
        if len(self.material_width) > self.buffer_size:
            self.le_pos.pop(0)
            self.ri_pos.pop(0)
            self.material_width.pop(0)

        return self.le_pos[-1], self.ri_pos[-1]


class Rectification:
    def __init__(self, buffer_size=10) -> None:
        self.buffer_size = buffer_size
        self.sta_loc = 0
        self.H_loc = 0
        self.abg = [0, 0, 0]  # alpha, beta, gamma
        self.size = 0
        self.le_freq = []
        self.ri_freq = []
        self.kappa_list = []
        self.locations = []
        self.smoothed_locations = []
        self.KF = []

    def rectify(self, px_l, f_cl, f_cr):
        self.le_freq.append(f_cl)
        self.ri_freq.append(f_cr)
        self.locations.append(px_l)
        self.kappa_list.append(1)
        self.smoothed_locations.append(self.resultSmooth(self.locations))
        self.size += 1

        alpha, beta, gamma = self.abg
        H_loc = self.H_loc
        cur_loc = self.smoothed_locations[-1]
        sta_loc = self.sta_loc
        d_l = cur_loc - sta_loc
        if abs(d_l) < H_loc:
            return f_cl, f_cr

        if self.size < 6:
            pass
        else:
            d_f = alpha * (f_cl - self.le_freq[-1]) - \
                  beta * (f_cr - self.le_freq[-1])
            d_m = self.smoothed_locations[-1] - self.smoothed_locations[-2]
            kappa = self.calculateKappa(d_f, d_m)
            self.kappa_list.append(kappa)
            k, b = self.mmse(self.kappa_list[0:-1], self.kappa_list[1:])
            self.KF.append(k * kappa + b)
        if len(self.KF) > 0:
            kappa = self.KF[-1]
        else:
            kappa = self.kappa_list[-1]

        if self.size > self.buffer_size:
            self.size -= 1
            for t_list in [self.le_freq, self.ri_freq, self.kappa_list,
                           self.locations, self.smoothed_locations, self.KF]:
                t_list.pop(0)  # not necessary to storage too many unused data

        fl, fr = self.calculateFrequency(
            f_cl, f_cr, alpha, beta, gamma, kappa, d_l)
        return fl, fr

    def calculateFrequency(self, f_cl, f_cr, alpha, beta, gamma, kappa, d_l):
        d_fr = -1 * (kappa * gamma * d_l) / beta
        d_fl = kappa * gamma * d_l + beta * d_fr
        d_fl = d_fl / alpha
        # xx
        fl = f_cl + d_fl
        fr = f_cr + d_fr
        return fl, fr

    def calculateKappa(self, d_f, d_lm):
        gamma = self.abg[-1]
        res = gamma * d_lm
        if res == 0:
            k = self.kappa_list[-1]
        else:
            k = d_f / (gamma * d_lm)
        return k

    def mmse(self, Xi, Yi):
        ##需要拟合的函数func :指定函数的形状
        def func(p, x):
            k, b = p
            return k * x + b

        # 偏差函数：x,y都是列表:这里的x,y更上面的Xi,Yi中是一一对应的

        def error(p, x, y):
            return func(p, x) - y

        p0 = [1, 0]
        Para = leastsq(error, p0, args=(Xi, Yi))
        k, b = Para[0]
        return k, b

    def resultSmooth(self, locations):
        loc = 0
        if len(locations) <= 5:
            loc = np.mean(locations)
        else:
            for num in locations[-5:]:
                loc += num / 2
            loc += locations[-1] / (2 ** 5)
        return loc
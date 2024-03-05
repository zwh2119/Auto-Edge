import os
import shutil
import time
import pandas as pd
import numpy as np
from scipy.signal import find_peaks

import requests


def http_request(url,
                 method=None,
                 timeout=None,
                 binary=True,
                 no_decode=False,
                 **kwargs):
    _maxTimeout = timeout if timeout else 300
    _method = 'GET' if not method else method

    try:
        response = requests.request(method=_method, url=url, **kwargs)
        if response.status_code == 200:
            if no_decode:
                return response
            else:
                return response.json() if binary else response.content.decode('utf-8')
        elif 200 < response.status_code < 400:
            print(f'Redirect URL: {response.url}')
        print(f'Get invalid status code {response.status_code} in request {url}')
    except Exception as e:
        print(e)


def get_stream_data():
    response = http_request(url='http://192.168.1.6:5000/imu', no_decode=True, stream=True)
    if response:
        content_disposition = response.headers.get('content-disposition')
        file_name = content_disposition.split('filename=')[1]
        file_path = os.path.join('debug', file_name)

        with open(file_path, 'wb') as f:
            response.raw.decode_content = True
            shutil.copyfileobj(response.raw, f)
        return file_path

    else:
        return None


def compare_np_data(file_path):
    csv_data = pd.read_csv(file_path)
    start_id, end_id = end_point_detection(csv_data)
    num_bin = len(start_id)
    for bi in range(num_bin):
        start_idx = int(start_id[bi])
        end_idx = int(end_id[bi]) + 1
        data = csv_data.iloc[start_idx:end_idx, [1, 6, 7, 8, 19, 20, 21]].values
        data = np.ascontiguousarray(data)

        file_name = f'temp_compare.npy'
        np.save(file_name, data)
        data_load = np.load(file_name)
        print('result: ',(data_load == data).all())


def end_point_detection(csv_data):
    linear_acceleration = csv_data.iloc[:, 19:22].values
    angular_velocity = csv_data.iloc[:, 6:9].values
    timestamp = csv_data.iloc[:, 1:2].values
    # transform unit
    # gyro : from deg to rad
    angular_velocity = angular_velocity / 180 * np.pi
    # linearacc: from g to m/s/s
    linear_acceleration = linear_acceleration * 9.81
    start_id, end_id = extractMotionLPMS3(timestamp, angular_velocity, linear_acceleration, 2)
    return start_id, end_id


def extractMotionLPMS3(lpms_time, lpms_gyro, lpms_linearacc, thre):
    x1 = np.sqrt(np.sum(lpms_linearacc ** 2, axis=1))
    x2 = np.sqrt(np.sum(lpms_gyro ** 2, axis=1))
    x = x1 + 5 * x2
    wlen = 10
    inc = 5
    win = np.hanning(wlen + 2)[1:-1]
    X = enframe(x, win, inc)
    X = np.transpose(X)
    fn = X.shape[1]
    time = lpms_time
    id = np.arange(wlen / 2, wlen / 2 + (fn - 1) * inc + 1, inc)
    id = id - 1
    frametime = time[id.astype(int)]
    En = np.zeros(fn)

    for i in range(fn):
        u = X[:, i]
        u2 = u * u
        En[i] = np.sum(u2)
    locs, pks = find_peaks(En, height=max(En) / 20, distance=15)
    pks = pks['peak_heights']
    # initialize startend_locs
    startend_locs = np.zeros((len(locs), 2), dtype=int)
    for i in range(len(locs)):
        si = locs[i] - 1
        while si > 0:
            if En[si] < thre:
                break
            si -= 1

        ei = locs[i] + 1
        while ei < len(En):
            if En[ei] < thre:
                break
            ei += 1

        startend_locs[i, 0] = si
        startend_locs[i, 1] = ei

    # delete repeat points
    startend_locs = np.unique(startend_locs, axis=0)

    # get id range
    start_id = id[startend_locs[:, 0]]
    end_id = id[startend_locs[:, 1] - 1]
    return start_id, end_id


def enframe(x, win, inc):
    nx = len(x)
    nwin = len(win)
    if nwin == 1:
        length = win
    else:
        length = nwin
    nf = int(np.fix((nx - length + inc) / inc))
    f = np.zeros((nf, length))
    indf = inc * np.arange(nf).reshape(-1, 1)
    inds = np.arange(1, length + 1)
    f[:] = x[indf + inds - 1]  # 对数据分帧
    if nwin > 1:
        w = win.ravel()
        f = f * w[np.newaxis, :]
    return f


if __name__ == '__main__':
    # while True:
    #     time.sleep(2)
    #     print(get_stream_data())

    compare_np_data('debug/12.csv')

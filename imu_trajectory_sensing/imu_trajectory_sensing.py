import numpy as np
# from scipy.integrate import cumtrapz
# from scipy.signal import find_peaks
# import pandas as pd


class ImuProcessor:
    def __init__(self):
        pass

    def __call__(self, file_path):
        R = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        output_ctx = {}
        output_ctx['result'] = []
        output_ctx['obj_num'] = []

        csv_data = pd.read_csv(file_path)
        start_id, end_id = self.end_point_detection(csv_data)
        num_bin = len(start_id)
        for bi in range(num_bin):
            start_idx = int(start_id[bi])
            end_idx = int(end_id[bi]) + 1
            data = csv_data.iloc[start_idx:end_idx, [1, 6, 7, 8, 19, 20, 21]].values
            data = np.ascontiguousarray(data)
            process_result = self.getPCA4(data, R)
            output_ctx['result'].append(process_result)
            output_ctx['obj_num'].append(len(process_result))

        return output_ctx

    def end_point_detection(self, csv_data):
        linear_acceleration = csv_data.iloc[:, 19:22].values
        angular_velocity = csv_data.iloc[:, 6:9].values
        timestamp = csv_data.iloc[:, 1:2].values
        # transform unit
        # gyro : from deg to rad
        angular_velocity = angular_velocity / 180 * np.pi
        # linearacc: from g to m/s/s
        linear_acceleration = linear_acceleration * 9.81
        start_id, end_id = self.extractMotionLPMS3(timestamp, angular_velocity, linear_acceleration, 2)
        return start_id, end_id

    def extractMotionLPMS3(self, lpms_time, lpms_gyro, lpms_linearacc, thre):
        x1 = np.sqrt(np.sum(lpms_linearacc ** 2, axis=1))
        x2 = np.sqrt(np.sum(lpms_gyro ** 2, axis=1))
        x = x1 + 5 * x2
        wlen = 10
        inc = 5
        win = np.hanning(wlen + 2)[1:-1]
        X = self.enframe(x, win, inc)
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

    def enframe(self, x, win, inc):
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

    def getPCA4(self, data, R):
        lpms_time = data[:, 0]
        lpms_gyro = data[:, 1:4]
        lpms_linearacc = data[:, 4:7]
        C = self.getRelativeRotation(lpms_gyro, lpms_time, R)
        linearacc_proj = self.getProjLA(lpms_linearacc, C)
        displacement = self.getDis(lpms_time, linearacc_proj)
        # 将NumPy数组转换为Python列表
        displace = displacement.tolist()
        return displace

    def getRelativeRotation(self, lpms_gyro, lpms_time, R):
        """
        Calculate the rotation matrix from body frame to global frame for motion data.

        Parameters:
        - lpms_gyro: Gyroscope data (angular velocity) in body frame.
        - lpms_time: Timestamps corresponding to the gyroscope data.
        - R: Initial rotation matrix.

        Returns:
        - C: Rotation matrices for each time step.
        """
        sample_num = lpms_gyro.shape[0]
        I = np.eye(3)

        # Initialize rotation matrix
        C = np.zeros((3, 3, sample_num))
        C[:, :, 0] = R

        for i in range(1, sample_num):
            w = lpms_gyro[i, :]
            wx, wy, wz = w
            t = lpms_time[i] - lpms_time[i - 1]
            B = np.array([[0, -wz * t, wy * t],
                          [wz * t, 0, -wx * t],
                          [-wy * t, wx * t, 0]])
            delta = np.linalg.norm(w * t)
            Ai = I + np.sin(delta) / delta * B + (1 - np.cos(delta)) / (delta ** 2) * np.dot(B, B)
            Ci = np.dot(C[:, :, i - 1], Ai)
            C[:, :, i] = Ci

        return C

    def getProjLA(self, watch_linearacc, C):
        """
        Rotate linear acceleration to the global frame.

        Parameters:
        - watch_linearacc: Local linear acceleration.
        - C: Rotation matrices for each time step.

        Returns:
        - linearacc_proj: Projected linear acceleration in the global frame.
        """

        linearacc_proj = np.zeros_like(watch_linearacc)
        sample_num = watch_linearacc.shape[0]

        for i in range(sample_num):
            # Get the rotation matrix from local to global frame
            Ci = C[:, :, i]

            # Get local linear acceleration
            linearacci = watch_linearacc[i, :]

            # Project current linear acceleration to global frame
            linearacc_proj[i, :] = np.dot(Ci, linearacci)

        return linearacc_proj

    def getDis(self, watch_time, linearacc_proj):
        """
        Estimate the displacement in the global frame via projected linear acceleration.

        Parameters:
        - watch_time: Timestamps corresponding to the linear acceleration data.
        - linearacc_proj: Projected linear acceleration in the global frame.

        Returns:
        - displacement: Displacement in the global frame.
        """

        watch_time = watch_time - watch_time[0]

        # Raw velocity
        velocity = np.copy(linearacc_proj)
        for i in range(3):
            velocity[:, i] = cumtrapz(linearacc_proj[:, i], watch_time[:], initial=0)

        # Calibrated velocity
        v_offset = velocity[-1, :]
        v_offset_unit = v_offset / watch_time[-1]
        v_subtract = np.outer(watch_time, v_offset_unit)
        v_calibrate = velocity - v_subtract

        # Displacement
        displacement = np.copy(v_calibrate)
        for i in range(3):
            displacement[:, i] = cumtrapz(v_calibrate[:, i], watch_time[:], initial=0)

        return displacement

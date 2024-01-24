import json
import numpy as np
from scipy.integrate import cumtrapz


class ImuProcessor:
    def __init__(self):
        pass

    def __call__(self, data):
        R = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]])
        process_result = self.getPCA4(data, R)

    def getPCA4(self, data, R):
        lpms_time = data[:, 0]
        lpms_gyro = data[:, 1:4]
        lpms_linearacc = data[:, 4:7]
        C = self.getRelativeRotation(lpms_gyro, lpms_time, R)
        linearacc_proj = self.getProjLA(lpms_linearacc, C)
        displacement = self.getDis(lpms_time, linearacc_proj)
        # 将NumPy数组转换为Python列表
        displace = displacement.tolist()
        json_data = json.dumps({"displacement": displace})
        # print(json_data)
        return json_data

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

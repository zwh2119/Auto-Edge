import time


class PIDController:
    def __init__(self):
        self.Kp = 1
        self.Ki = 0.1
        self.Kd = 0.01

        self.min_value = -3
        self.max_value = 3

        self.cur_time = time.time()
        self.last_time = self.cur_time

        self.setpoint = 0

        self.previous_error = 0
        self.integral = 0

    def clear(self):
        self.previous_error = 0
        self.integral = 0
        self.cur_time = time.time()
        self.last_time = self.cur_time

    def check_pid_parameter(self):
        print(f'kp:{self.Kp}, ki:{self.Ki}, kd:{self.Kd}')

    def reset_pid_parameter(self):
        self.Kp = 1
        self.Ki = 0.1
        self.Kd = 0.01

    def set_setpoint(self, setpoint):
        self.setpoint = setpoint

    def update(self, current_value):

        error = self.setpoint - current_value
        self.cur_time = time.time()
        dt = self.cur_time - self.last_time
        self.integral += error
        derivative = (error - self.previous_error) / dt if dt > 0 else 0
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative
        self.previous_error = error

        # ## 控制边际，防止过度调控（自动化领域需要，这里是否需要保留？）
        # if output < self.min_value:
        #     output = self.min_value
        # elif output > self.max_value:
        #     output = self.max_value

        return output

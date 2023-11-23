import cv2
import multiprocessing
import threading


class TestClass:
    def __init__(self, video_path):
        self.video_path = video_path
        self.video_cap = cv2.VideoCapture(video_path)

    def run(self):
        print(f'{self.video_path} start!')
        while True:
            ret, frame = self.video_cap.read()

            while not ret:
                print(f'no frame receive of {self.video_path}')
            print(f'get one frame of {self.video_path}')


if __name__ == '__main__':
    videos = [
        'traffic0.mp4',
        'traffic1.mp4',
        'traffic2.mp4'
    ]

    for video in videos:
        test = TestClass(video)
        threading.Thread(target=test.run).start()

    # test = TestClass(videos[0])
    # test.run()

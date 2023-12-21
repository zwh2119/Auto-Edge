import cv2
from rtsp import Server

server = Server(port=8554, path='/live', streaming_type='rtp')
cap = cv2.VideoCapture('../test/traffic0.mp4')
server.add_source(cap)
server.start()

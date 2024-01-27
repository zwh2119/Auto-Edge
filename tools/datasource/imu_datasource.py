from flask import Flask, send_file
import os
import argparse

app = Flask(__name__)

file_directory = None
file_list = None
file_index = 0


@app.route("/imu", methods=["GET"])
def get_file():
    global file_index
    file_name = file_list[file_index]
    file_path = os.path.join(file_directory, file_name)
    file_index = (file_index + 1) % len(file_list)
    return send_file(file_path, download_name=file_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', default='imu/1',help='dataset dir')
    parser.add_argument('--port', default=5000, type=int, help='imu data port')

    args = parser.parse_args()

    file_directory = args.dataset
    file_list = os.listdir(file_directory)

    app.run(host='0.0.0.0', port=args.port)

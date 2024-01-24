from flask import Flask, send_file
import os

app = Flask(__name__)

file_directory = "/Users/wenyidai/GitHub/multi-task-ce-framework/imu/6-axis"
file_list = os.listdir(file_directory)
file_index = 0


@app.route("/", methods=["GET"])
def get_file():
    global file_index
    file_name = file_list[file_index]
    file_path = os.path.join(file_directory, file_name)
    file_index = (file_index + 1) % len(file_list)
    return send_file(file_path, download_name=file_name)


if __name__ == "__main__":
    app.run()

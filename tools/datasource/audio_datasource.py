from flask import Flask, send_file
import os
import random

app = Flask(__name__)

dataset_folder = '/Users/wenyidai/GitHub/multi-task-ce-framework/audio_example/dataset'
files = os.listdir(dataset_folder)
file_index = 0


@app.route('/', methods=['GET'])
def get_file():
    global file_index
    file_path = os.path.join(dataset_folder, files[file_index])
    file_name = files[file_index]  # Get the file name
    file_index = (file_index + 1) % len(files)

    return send_file(file_path, mimetype='audio/wav', as_attachment=True, download_name=file_name)


if __name__ == '__main__':
    app.run()
    
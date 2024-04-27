import os
import shutil


class FileOps:
    @staticmethod
    def save_data_file(task, file_data):
        file_path = task.get_file_path()
        with open(file_path, 'wb') as buffer:
            buffer.write(file_data)

    @staticmethod
    def remove_data_file(task):
        file_path = task.get_file_path()
        if os.path.exists(file_path):
            shutil.rmtree(file_path)

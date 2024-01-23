class Task:
    def __init__(self, data: dict, file: str):
        self.metadata = data
        self.file_path = file

    def __lt__(self, other):
        return self.metadata['priority']['priority'] > other.metadata['priority']['priority']

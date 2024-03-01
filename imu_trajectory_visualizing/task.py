class Task:
    def __init__(self, data: dict, file: str):
        self.metadata = data
        self.file_path = file

    def __lt__(self, other):
        index = self.metadata['cur_flow_index']
        return self.metadata['priority'][index]['priority'] > other.metadata['priority'][index]['priority']

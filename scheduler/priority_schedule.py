import bisect
import json
import os
import time


class PriorityProfiler:
    def __init__(self, importance_weight, urgency_weight, deadline):
        self.urgency_w = urgency_weight
        self.importance_w = importance_weight
        self.deadline = deadline

        self.priority_level_num = 10

    def get_task_priority(self, task_name, data):
        importance = self.get_task_importance(data)
        urgency = self.get_task_urgency(task_name, data)
        priority = round(importance * self.importance_w + urgency * self.urgency_w)

        data['importance'] = importance
        data['urgency'] = urgency
        data['priority'] = priority

        return data

    def get_task_urgency(self, task_name, data):
        remaining_time = self.get_relative_remaining_time(data['start_time'])
        urgency_threshold_list = self.get_urgency_threshold(task_name)
        self.update_urgency_history(task_name, remaining_time)

        if urgency_threshold_list is None:
            return 0
        else:
            urgency = 0
            for value in urgency_threshold_list:
                if remaining_time >= value:
                    urgency += 1
                else:
                    break
        return urgency

    def get_task_importance(self, data):
        assert 'importance' in data
        return data['importance']

    def get_urgency_threshold(self, task_name):
        urgency_list = self.get_urgency_history(task_name)
        if len(urgency_list) < self.priority_level_num - 1:
            return None
        else:
            # collect last num of each urgency unit as threshold
            urgency_threshold = self.split_list_into_chunks_last(urgency_list, self.priority_level_num - 1)
            return urgency_threshold

    def get_urgency_history(self, task_name):
        if not os.path.exists(task_name):
            return []

        with open(task_name) as f:
            urgency_history = json.load(f)
        return urgency_history

    def update_urgency_history(self, task_name, urgency):
        if os.path.exists(task_name):
            with open(task_name, 'r') as f:
                urgency_history = json.load(f)
        else:
            urgency_history = []

        bisect.insort(urgency_history, urgency)
        with open(task_name, 'w') as f:
            json.dump(urgency_history, f)

    def get_relative_remaining_time(self, start_time):
        return (time.time() - start_time) / self.deadline

    def split_list_into_chunks_last(self, list_input, n):
        chunk_size, remainder = divmod(len(list_input), n)
        chunks_last = []
        start = 0
        for i in range(n):
            end = start + chunk_size + (1 if i < remainder else 0)
            chunks_last.append(list_input[end - 1])
            start = end

        return chunks_last

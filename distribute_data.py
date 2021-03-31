

class distribute_data:
    def __init__(self, num_splits, data):
        self.data = data
        self.num_splits = num_splits

    def split(self):
        end = -1
        num_data_per_split = len(self.data) // self.num_splits
        for i in range(self.num_splits):
            # if we are at the last one
            if i is self.num_splits-1:
                start = end + 1
                yield self.data[start:]
                break
            start = i * num_data_per_split
            end = (i+1) * num_data_per_split - 1
            yield self.data[start:end+1]



class distribute_data:
    def __init__(self, num_nodes, data):
        self.data = data
        self.num_nodes = num_nodes

    def split(self):
        end = -1
        num_data_per_node = len(self.data) // self.num_nodes
        for i in range(self.num_nodes):
            # if we are at the last one
            if i is self.num_nodes-1:
                start = end + 1
                yield self.data[start:]
                break
            start = i * num_data_per_node
            end = (i+1) * num_data_per_node - 1
            yield self.data[start:end+1]

import threading
import net_protocol


class get_statistics:
    def __init__(self, nodes):
        self.nodes = nodes
        self.stats = dict.fromkeys(nodes)
        self.threads = []

    def start_listen(self):
        for nid in self.nodes:
            thread = threading.Thread(target=self.__get_node_stats, args=(nid,), daemon=True)
            thread.start()
            self.threads.append(thread)

    def __get_node_stats(self, nid):
        while True:
            stats = net_protocol.recv_stats(self.nodes[nid])
            if stats:
                self.stats.update(stats)

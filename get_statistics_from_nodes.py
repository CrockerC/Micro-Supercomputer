import threading
import net_protocol


class get_statistics_from_nodes:
    def __init__(self, nodes, window_log='window.txt'):
        self.window_log = window_log
        self.nodes = nodes
        self.stats = dict.fromkeys(nodes)
        self.threads = []
        self.sem = threading.Semaphore()
        self.wait_for_ans = threading.Event()
        self.got_ans = dict.fromkeys(nodes)

    def start_listen(self):
        for nid in self.nodes:
            thread = threading.Thread(target=self.__get_node_stats, args=(nid,), daemon=True)
            thread.start()
            self.threads.append(thread)

    def __get_node_stats(self, nid):
        while True:
            stats = net_protocol.recv_stats(self.nodes[nid])
            if stats:
                # if we are just getting the bash output, it will be a string
                if isinstance(stats[nid], str):
                    self.sem.acquire()
                    print("Shell output for node {}: \n{}".format(nid, stats[nid]))
                    self.got_ans[nid] = True
                    if all(self.got_ans.values()):
                        self.wait_for_ans.set()
                    self.sem.release()
                    with open(nid + self.window_log, 'a') as f:
                        f.write(stats[nid])
                    return

                # otherwise do normal stat operations (it will be a dict)
                else:
                    self.stats.update(stats)

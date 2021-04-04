import os
import time


class handle_stats:
    def __init__(self, stat_listener, log_file='sensors_log.csv'):
        self.stat_listener = stat_listener
        self.log_file = log_file
        for node in self.stat_listener.nodes:
            path = node + ":" + self.log_file
            if not os.path.isfile(path):
                first_line = "time,cpu_usage,cpu_temp,ram_used,ram_available,ram_percent,python_ram_used,swap_used,swap_free,swap_percent,\n"
                with open(path, "w") as f:
                    f.write(first_line)

    def handle(self):
        while True:
            self.stat_listener.update_signal.wait()
            datetime = time.strftime("[%m/%d/%Y %H:%M:%S]", time.localtime())
            for node in self.stat_listener.nodes:
                node_stats = self.stat_listener.stats[node]
                path = node + ":" + self.log_file

                line = [datetime, node_stats["cpu_usage"], node_stats["cpu_temperature"],
                        node_stats["ram"]['used'], node_stats["ram"]['available'], node_stats["ram"]['percent'],
                        node_stats["python_ram_usage"],
                        node_stats["swap"]['used'], node_stats["swap"]['free'], node_stats["swap"]['percent'], "\n"]

                with open(path, "a") as f:
                    f.write(",".join(line))

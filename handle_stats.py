import os
import time


class handle_stats:
    def __init__(self, stat_listener, log_file='_sensors_log.csv'):
        self.stat_listener = stat_listener
        self.log_file = log_file
        for node in self.stat_listener.nodes:
            self.__init_log(node)

    def handle(self):
        while True:
            self.stat_listener.update_signal.wait()
            datetime = time.strftime("[%m/%d/%Y - %H:%M:%S]", time.localtime())
            for node in self.stat_listener.nodes:
                node_stats = self.stat_listener.stats[node]
                if not node_stats:
                    continue
                factor = 1024*1024
                line = [datetime, node_stats["cpu_usage"], node_stats["cpu_temperature"],
                        node_stats["ram"]['used']/factor, node_stats["ram"]['available']/factor, node_stats["ram"]['percent'],
                        node_stats["python_ram_usage"]/factor, round(node_stats["python_ram_usage"] / node_stats["ram"]["total"] * 100, 1),
                        node_stats["swap"]['used']/factor, node_stats["swap"]['available']/factor, node_stats["swap"]['percent'], "\n"]

                for i, item in enumerate(line):
                    if isinstance(item, float):
                        item = round(item, 1)
                    line[i] = str(item)

                self.__log(line, node)
            self.stat_listener.update_signal.clear()

    def __log(self, data, node):
        with open(node + "_" + self.log_file, "a") as f:
            f.write(",".join(data))

    def __init_log(self, node):
        path = node + "_" + self.log_file
        if not os.path.isfile(path):
            first_line = "time,cpu_usage,cpu_temp,ram_used,ram_available,ram_percent,python_ram_used,python_ram_percent,swap_used,swap_free,swap_percent,\n"
            with open(path, "w") as f:
                f.write(first_line)

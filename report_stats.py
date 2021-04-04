import psutil
import gpiozero
import sys


class report_stats:
    def __init__(self):
        self.is_pi = self.__is_pi()

    @staticmethod
    def __is_pi():
        try:
            with open('/sys/firmware/devicetree/base/model', 'r') as m:
                if 'raspberry pi' in m.read().lower():
                    return True
                else:
                    return False
        except FileNotFoundError:
            pass
        return False

    @staticmethod
    def get_cpu_usage():
        return {"cpu_usage": psutil.cpu_percent(interval=.1)}

    @staticmethod
    def get_ram_usage():
        ram = psutil.virtual_memory()
        return {"ram": {"total": ram.total, "used": ram.used, "available": ram.available, "percent": ram.percent}}

    @staticmethod
    def get_swap_usage():
        ram = psutil.swap_memory()
        return {"swap": {"total": ram.total, "used": ram.used, "available": ram.free, "percent": ram.percent}}

    def get_cpu_temperature(self):
        if self.is_pi:
            return {"cpu_temperature": gpiozero.CPUTemperature()}
        else:
            return {"cpu_temperature": False}

    @staticmethod
    def get_python_ram_usage():
        if sys.platform == "win32":
            name = "python.exe"
        elif sys.platform == "linux":
            name = "python3"
        else:
            return False
        ram = 0
        processes = list(psutil.process_iter())
        for process in processes:
            if process.name() == name:
                ram += psutil.Process(process.pid).memory_info().rss

        return {"python_ram_usage": ram}

    def get_stats(self):
        stats = dict()
        stats.update(self.get_cpu_usage())
        stats.update(self.get_ram_usage())
        stats.update(self.get_swap_usage())
        stats.update(self.get_cpu_temperature())
        stats.update(self.get_python_ram_usage())

        return stats


if __name__ == "__main__":
    import time
    stats = report_stats()
    start = time.time()
    print(stats.get_cpu_usage())
    print(time.time() - start)
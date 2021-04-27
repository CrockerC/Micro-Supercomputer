import time
import threading


class my_timer:
    def __init__(self):
        self.__threads = dict()  # {tid: True/False} t/f for if the timer is running for that thread
        self.__total = 0
        self.__start = None
        self.__sem = threading.Semaphore()

    def start(self, tid):
        self.__sem.acquire()
        self.__threads.update({tid: True})
        if self.__start is None:
            self.__start = time.perf_counter()
        self.__sem.release()

    def pause(self, tid):
        self.__sem.acquire()
        self.__threads.update({tid: False})
        if not any(self.__threads.values()):
            self.__total += (time.perf_counter() - self.__start)
            self.__start = None
        self.__sem.release()

    def stop(self):
        self.__sem.acquire()
        for thread in self.__threads:
            self.__threads.update({thread: False})
        self.__total += (time.time() - self.__start)
        self.__start = None
        self.__sem.release()

    def time(self):
        return self.__total

import os
import threading


class get_bash:
    def __init__(self, bash):
        threading.Thread(target=self.__exec_bash, args=(bash,)).start()

    @staticmethod
    def __exec_bash(bash):
        os.system(bash)

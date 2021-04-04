import subprocess


class get_bash:
    def __init__(self):
        pass

    @staticmethod
    def exec_bash(bash):
        sub = subprocess.Popen(bash, shell=True, stdout=subprocess.PIPE)
        return sub.stdout.read()

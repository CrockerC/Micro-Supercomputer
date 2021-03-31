import threading
import typing
import net_protocol


class multipleListens:
    def __init__(self, socks: typing.Dict, perf=False):
        self.socks = socks
        self.perf = perf
        self.listens = dict()
        self.signalRemove = threading.Event()

        self.ret = threading.Semaphore()  # semaphore to protect self.value
        self.got = threading.Event()  # signal for self.loop to yeild the data in self.value
        # self.vSafe = threading.Event()  # signal to self.listen that it is safe to write to self.value
        self.value = []

        self.close = threading.Event()

        # self.vSafe.set()

        self.updateListens()

    def updateListens(self):
        for sid in self.socks.keys():
            sock = self.socks[sid]
            if sock not in self.listens:
                self.listens.update({sock: threading.Thread(target=self.listen, args=(sock, sid))})
                self.listens[sock].start()

    # loop is meant to be run immediately after the init it called, ie:

    # listen = multipleListens(socks)
    # for data in listen.loop():
    #   handler(data)
    def loop(self):
        count = 0
        while count < len(list(self.socks.keys())):
            count += 1
            # wait for the buffer to be flushed before closing
            if self.close.isSet() and not self.value:
                return

            self.got.wait()  # wait until we have data for self.value
            self.ret.acquire()  # acquire the semaphore

            yield self.value.pop(0)  # yield the data to the caller

            if not self.value:
                self.got.clear()  # signal that there is no value in self.value

            self.ret.release()  # release the semaphore

        self.exit()

    def listen(self, sock, sid):
        if self.close.isSet():
            return

        if self.perf:
            try:
                data, speed = net_protocol.recv_processed(sock, st=True)  # get data from the socket
            except Exception as ext:
                if ext == KeyboardInterrupt:
                    raise KeyboardInterrupt
                data = False
                speed = False

            self.ret.acquire()  # acquire the semaphore
            self.value.append((data, speed, sid))  # write the data to self.value

        else:
            try:
                data = net_protocol.recv_processed(sock)
            except Exception as ext:
                if ext == KeyboardInterrupt:
                    raise KeyboardInterrupt
                data = False

            self.ret.acquire()
            self.value.append((data, 0, sid))

        self.got.set()  # signal that we can now give the value to the caller of self.loop
        self.ret.release()  # release the semaphore

    def exit(self):
        self.close.set()
        del self
import threading
import typing
import net_protocol


class multipleListens:
    def __init__(self, socks: typing.Dict, timer=None):
        self.socks = socks
        self.listens = dict()
        self.signalRemove = threading.Event()
        self.timer = timer

        self.value = {}
        self.got = {}
        for key in self.socks:
            self.got.update({key: threading.Event()})  # signal for self.loop to yield the data in self.value

        self.close = threading.Event()
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
        keys = list(self.socks.keys())
        while count < len(list(self.socks.keys())):
            next_key = keys[count]
            count += 1
            # wait for the buffer to be flushed before closing
            if self.close.isSet() and not self.value:
                return

            self.got[next_key].wait()  # wait until we have data for self.value
            yield self.value[next_key]  # yield the data to the caller
        self.exit()

    def listen(self, sock, sid):
        if self.close.isSet():
            return
        try:
            data = net_protocol.recv_processed(sock, timer=self.timer)
        except Exception as ext:
            if ext == KeyboardInterrupt:
                raise KeyboardInterrupt
            data = False

        self.value.update({sid: (data, sid)})  # write the data to self.value
        self.got[sid].set()  # signal that we can now give the value to the caller of self.loop

    def exit(self):
        self.close.set()
        del self

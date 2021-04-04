import socket
import struct
import threading
import psutil
import warnings
import time
import orjson as json
import zstd
import sys


def get_ip():
    adapters = psutil.net_if_addrs()

    if sys.platform == "win32":
        # ethernet has priority over wifi
        if "Ethernet" in adapters:
            adapter = "Ethernet"
        elif "Wi-Fi" in adapters:
            warnings.warn("Using Wifi instead of ethernet! This can be dangerous if the wifi network is connected to the internet!")
            adapter = "Wi-Fi"
        else:
            warnings.warn("Cannot find ethernet or wifi adapter! Defaulting to socket.gethostname()")
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)

        for prot in adapters[adapter]:
            if prot.family is socket.AF_INET:
                return prot.address

    elif sys.platform == "linux":
        adapter = None
        if "eth0" in adapters:
            for addr_type in adapters["eth0"]:
                if addr_type.family is socket.AF_INET:
                    return addr_type.address

        if "wlan0" in adapters:
            for addr_type in adapters["wlan0"]:
                if addr_type.family is socket.AF_INET:
                    return addr_type.address

        if not adapter:
            warnings.warn("Cannot find ethernet or wifi adapter! Defaulting to socket.gethostname()")
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)

    else:
        raise Exception("This is only compatible with windows and linux!")


def recv_data(sock, timeout=None):
    if timeout is not None:
        sock.settimeout(timeout)
    lenData = __recvall(sock, 4)
    if not lenData:
        return False
    lenData = struct.unpack('>I', lenData)[0]
    data = bytes(__recvall(sock, lenData))
    data = zstd.decompress(data)
    if timeout is not None:
        sock.settimeout(None)
    return data


def __recvall(sock, n):
    data = bytearray()
    try:
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return False
            data.extend(packet)
    except:
        return False
    return data


def recv_data_no_decompress(sock, timeout=None):
    if timeout is not None:
        sock.settimeout(timeout)
    lenData = __recvall(sock, 4)
    if not lenData:
        return False
    lenData = struct.unpack('>I', lenData)[0]
    data = bytes(__recvall(sock, lenData))
    if timeout is not None:
        sock.settimeout(None)
    return data


def addLenU(data):
    return struct.pack('>I', len(data)) + data


# this crashes when the reciever disconnects
# though it may stop doing that now that its threaded, since the thread will crash and not the main program
# do threads have crash signals that i can listen for to detect the disconnection?
def sendall(sock, data):
    # there is a good reason why the json.dumps is not here, please don't put it here
    if isinstance(data, str):
        data = bytes(data, "utf-8")
    size = len(data)
    data = zstd.compress(data, 1)
    data = addLenU(data)
    threading.Thread(target=sock.sendall, args=(data,)).start()
    return size  # the size BEFORE compression


def send_task(task_name, code, sock, data, perf=True):
    if perf:
        start = time.perf_counter()

    # todo, is wrapping this in a list good? I mean, it solves a problem i was having, but does it cause problems with generalizing the format?
    data = json.dumps((task_name, code, [data]))
    data_size = sendall(sock, data)
    if perf:
        send_time = time.perf_counter() - start + .0000001
        return data_size / (1024 * 1024), send_time
    return 0, 0


def recv_task(sock, perf=True):
    data = recv_data_no_decompress(sock)
    if perf:
        start = time.perf_counter()

    if not data:
        return False, False, False, False, False
    size = len(data)
    data = zstd.decompress(data)
    name, task, data = json.loads(data)

    if perf:
        recv_time = time.perf_counter() - start + .0000001
        return name, task, data, size / (1024 * 1024), recv_time
    return name, task, data, 0, 0


def send_processed(sock, data, nid, perf=True):
    if perf:
        start = time.perf_counter()
    data = json.dumps({nid: data})
    size = sendall(sock, data)
    if perf:
        send_time = time.perf_counter() - start + .0000001
        return size / (1024 * 1024), send_time
    return 0, 0


def recv_processed(sock, timeout=None, perf=True):
    sock.settimeout(timeout)
    data = recv_data_no_decompress(sock)
    if not data:
        return False, False, False

    if perf:
        start = time.perf_counter()

    size = len(data)
    data = zstd.decompress(data)
    data = json.loads(data)
    if perf:
        recv_time = time.perf_counter() - start + .0000001
        return data, size / (1024 * 1024), recv_time
    return data, 0, 0


def send_stats(sock, data, nid):
    data = json.dumps({nid: data})
    if isinstance(data, str):
        data = bytes(data, "utf-8")
    data = zstd.compress(data, 1)
    data = addLenU(data)
    sock.sendall(data)


def recv_stats(sock):
    return recv_processed(sock, perf=False)[0]


def send_command(sock, bash):
    threading.Thread(target=send_task, args=("system command", bash, sock, (1, 1, 1))).start()

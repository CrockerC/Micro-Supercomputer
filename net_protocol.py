import socket
import struct
#import bz2
import threading
import psutil
import warnings
import time
import json
import brotli


def get_ip():
    adapters = psutil.net_if_addrs()
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


def recv_data(sock, timeout=None):
    if timeout is not None:
        sock.settimeout(timeout)
    lenData = __recvall(sock, 4)
    if not lenData:
        return False
    lenData = struct.unpack('>I', lenData)[0]
    data = bytes(__recvall(sock, lenData))
    data = brotli.decompress(data)
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


def addLenU(data):
    return struct.pack('>I', len(data)) + data


# this crashes when the reciever disconnects
# though it may stop doing that now that its threaded, since the thread will crash and not the main program
# do threads have crash signals that i can listen for to detect the disconnection?
def sendall(sock, data):
    # there is a good reason why the json.dumps is not here, please dont put it here
    if isinstance(data, str):
        data = bytes(data, "utf-8")
    data = brotli.compress(data, quality=1)
    data = addLenU(data)
    threading.Thread(target=sock.sendall, args=(data,)).start()


def send_task(sock, task_name, code, data):
    data = json.dumps((task_name, code, data))
    sendall(sock, data)


def recv_task(sock):
    data = recv_data(sock)
    if not data:
        return False, False, False

    return json.loads(data)


def send_processed(sock, data, nid):
    data = json.dumps({nid: data})
    sendall(sock, data)


def recv_processed(sock, timeout=None):
    sock.settimeout(timeout)
    data = recv_data(sock)
    if data:
        return json.loads(data)
    else:
        return False

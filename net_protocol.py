import socket
import struct
import dill as pickle
import bz2
import threading
import psutil
import warnings


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

    for type in adapters[adapter]:
        if type is socket.AF_INET:
            return type.address


def recv_data(sock, timeout=None, st=False):
    if timeout is not None:
        sock.settimeout(timeout)
    lenData = __recvall(sock, 4)
    if not lenData:
        return False
    lenData = struct.unpack('>I', lenData)[0]
    data = bytes(__recvall(sock, lenData))
    data = bz2.decompress(data)
    if timeout is not None:
        sock.settimeout(None)
    if st:
        return data, lenData+4  # lenData+4 in bytes
    else:
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
def sendall(sock, data):
    n_data = bz2.compress(data)
    data = addLenU(n_data)
    threading.Thread(target=sock.sendall, args=(data,)).start()


def send_task(sock, code, task_name, data):
    n_data = pickle.dumps((task_name, code, data))
    sendall(sock, n_data)


def recv_task(sock):
    data = recv_data(sock)
    if not data:
        return False, False, False
    return pickle.loads(data)


def send_processed(sock, data):
    id = socket.gethostbyname(socket.gethostname())
    data = pickle.dumps({id: data})
    sendall(sock, data)


def recv_processed(sock, timeout=None, st=False):
    sock.settimeout(timeout)
    data = recv_data(sock, st=st)
    if data:
        return pickle.loads(data)
    else:
        return False

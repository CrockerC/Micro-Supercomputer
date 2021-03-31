import socket
import struct
import dill as pickle
import inspect
import bz2
import threading


def recv_data(sock, timeout=None, st=False):
    if timeout is not None:
        sock.settimeout(timeout)
    lenData = __recvall(sock, 4)
    if not lenData:
        return False
    lenData = struct.unpack('>I', lenData)[0]
    data = bytes(__recvall(sock, lenData))
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
    data = addLenU(data)
    threading.Thread(target=sock.sendall, args=(data,)).start()


def send_task(sock, code, task_name, data):
    n_data = pickle.dumps((task_name, code, data))
    n_data = bz2.compress(n_data)
    sendall(sock, n_data)


def recv_task(sock):
    data = recv_data(sock)
    if not data:
        return False, False, False
    data = bz2.decompress(data)
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

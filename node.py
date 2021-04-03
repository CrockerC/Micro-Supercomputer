import threading
import pathos.multiprocessing as mp
import socket
import net_protocol
import time
import types
import numpy as np
import multiprocess as ms
import sympy

# todo, add timestamps to logs

# todo, right now there is no secondary data reporting, so the secondary_con is not used
# todo, don't delete it lol


def main(primary_port=12321, secondary_port=12322):
    primary_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = net_protocol.get_ip()
    primary_sock.bind((ip_address, primary_port))
    primary_sock.listen(1)

    secondary_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = net_protocol.get_ip()
    secondary_sock.bind((ip_address, secondary_port))
    secondary_sock.listen(1)

    print("Waiting for connection to master")
    while True:
        try:
            master_con, secondary_con = listen(primary_sock, secondary_sock)
            do_task(master_con, ip_address)
        except KeyboardInterrupt:
            print("Cancelled by user!")
            break
    # the node is now added and ready to accept tasks


def do_task(master_con, ip):
    while True:
        t1 = time.perf_counter()
        name, task, data, data_size, data_time = net_protocol.recv_task(master_con)
        recv_time = time.perf_counter() - t1 + .000000000001
        print("Time spent waiting on the task: {:.3f}s".format(recv_time))
        # note that this includes waiting for the socket to get data
        if data_size and data_time:
            print("The protocol communication recv overhead went at {:.4f}MB/s for {:.4f}s".format(data_size / data_time, data_time))

        if not task:
            print("Lost connection to master, listening for connection")
            break

        # this takes the string code and converts it into a usable class
        # note that this method is a huge security risk
        # the network that the nodes run on -needs- to be isolated from the internet
        # it also needs to contain any imports that you need
        # they also have to be already installed, this crap doesnt bring dependencies with it
        # it also does NOT work with multiprocessing for some reason
        # instead of multiprocessing you have to use pathos.multiprocessing.ProcessPool, this can be used as a drop in for multiprocessing.pool
        # note that that is the only (useful) feature of multiprocessing that carries over into pathos.multiprocessing
        exec(task)
        task = eval('%s' % name)

        print("Got task, running")
        if data is not None:
            # note that the data MUST be in a list or a tuple (even if there is only one argument) (unless there is no argument)
            try:
                task = task(*data)
            except TypeError:
                raise TypeError("data MUST be either a tuple, a list, or None\n"
                                "If you are also getting an error like this '__init__() takes 2 positional arguments but 11 were given'\n"
                                "then you probably need to wrap your data in a list like so [data]")
        else:
            task = task()

        start = time.perf_counter()
        data = task.run()
        print("Task completed in {:.3f}s".format(time.perf_counter()-start))

        data_size, data_time = net_protocol.send_processed(master_con, data, ip)
        if data_size and data_time:
            print("Time spent sending processed data {:.3f}s".format(data_time))
            print("The protocol communication send overhead went at {:.4f}MB/s for {:.4f}s".format(data_size / data_time, data_time))

        del data, task


def listen(primary_sock, secondary_sock):
    call = bytes("x gon", 'utf-8')
    response = bytes("give it to ya", 'utf-8')
    connected = False
    master_con = None
    secondary_con = None
    while not connected:
        try:
            master_con, addr = primary_sock.accept()
            mess = net_protocol.recv_data(master_con)
            if mess == call:
                net_protocol.sendall(master_con, response)
                secondary_con, addr = secondary_sock.accept()
                connected = True
                print("Connected to master")
            else:
                master_con.exit()
                print("Incoming connection failed, waiting for new connection")
        except:
            if master_con:
                master_con.close()

            if secondary_con:
                secondary_con.close()
            print("Incoming connection failed, waiting for new connection")

    return master_con, secondary_con


if __name__ == "__main__":
    main()

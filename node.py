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


def main(port=12321):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ip_address = net_protocol.get_ip()
    s.bind((ip_address, port))
    s.listen(1)

    print("Waiting for connection to master")
    while True:
        try:
            master_con = listen(s)
            do_task(master_con)
        except KeyboardInterrupt:
            print("Cancelled by user!")
            break
    # the node is now added and ready to accept tasks


def do_task(master_con):
    while True:
        name, task, data = net_protocol.recv_task(master_con)

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

        start = time.time()
        data = task.run()
        print("Task completed in {}s".format(time.time()-start))

        net_protocol.send_processed(master_con, data)
        del data, task


def listen(s):
    call = bytes("x gon", 'utf-8')
    response = bytes("give it to ya", 'utf-8')
    connected = False
    master_con = None
    while not connected:
        try:
            master_con, addr = s.accept()
            mess = net_protocol.recv_data(master_con)
            if mess == call:
                net_protocol.sendall(master_con, response)
                connected = True
                print("Connected to master")
            else:
                master_con.exit()
                print("Incoming connection failed, waiting for new connection")
        except:
            if master_con:
                master_con.close()
            print("Incoming connection failed, waiting for new connection")

    return master_con


if __name__ == "__main__":
    main()

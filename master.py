import net_protocol
import scan_ip
import distribute_data
import util
import async_listen
import psutil
from multiprocessing.pool import ThreadPool
import functools
import sys
import get_statistics_from_nodes
import send_bash
import time

CPU_COUNT = psutil.cpu_count(logical=False)
THREAD_COUNT = CPU_COUNT ** 2


# todo, make better comments before i forget how it all works

# todo, i could implement a thing that lets it detect when a node is lost and divy up its data to the rest to avoid loss of data
# todo, but idk that seems like a bit of an edge case, but for very long running tasks like generating primes, something like that could be important
# todo, wait dont have it divy up the work, just give it to a node, giving it to all of them is unncessarily complicated
# todo, thatll be part of v2

# todo, my laptop went to sleep and the master didnt detect it. It also seemed to freeze the whole thing

# todo, implement timestamps and logging for everything
# todo, strftime("[%m/%d/%Y %H:%M:%S]", time.localtime()) gives this [04/02/2021 00:53:24]
# todo, there is also probably a logging library

def main(task, data, data_generator=None, processed_handler=print, handler_args=tuple(), **kwargs):
    # parted is how many rounds of processing you want to split your total data into

    scan = scan_ip.scan_ip()
    nodes = scan.scan_space()
    if nodes == {}:
        print("The master could not find any nodes, quitting")
        sys.exit(0)

    get_stats = get_statistics_from_nodes.get_statistics_from_nodes(scan.get_secondary_dict())
    get_stats.start_listen()  # use get_stats.stats to get the various stats for all of the nodes

    if data_generator is None:
        # note that its best to split this so that there are 16 sets of data per pi (cause 4 cores * 4 for mp pool overhead)
        # note but this may differ based on your application and whether you use mp pools or not
        big_data = distribute_data.distribute_data(len(nodes), data)
        big_data = list(big_data.split())
    else:
        big_data = data_generator(num_per_node=THREAD_COUNT, num_nodes=len(nodes), **kwargs)

    task_name = task.split(".")[0]
    with open(task, "r") as f:
        task = f.read()

    for little_data in big_data:
        little_data = distribute_data.distribute_data(len(nodes.keys()), little_data)
        little_data = little_data.split()

        # send each node's data to it synchronously
        # in v2 itll do it asynchronously, although idk how ill handle ordering
        sizes = []
        times = []

        # todo, having this be threaded breaks the time measurements
        # todo, since the json isnt threadable, maybe its a better idea to use multiprocesing
        pool = ThreadPool()
        send_partial = functools.partial(net_protocol.send_task, task_name, task)
        results = list(pool.starmap(send_partial, zip(nodes.values(), list(little_data))))

        for result in results:
            data_size, data_time = result
            sizes.append(data_size)
            times.append(data_time)

        avg_size = sum(sizes) / len(sizes)
        avg_time = sum(times) / len(times)
        print("The protocol communication send overhead went at {:.4f}MB/s for {:.4f}s".format(avg_size / avg_time, sum(times)))
        # free up ram
        del little_data

        del_list = []
        # get the results from each node asynchronously
        # but it also gets them in the same order they were sent out in
        # i know, its trippy lol
        listen = async_listen.multipleListens(nodes.copy())
        sizes = []
        times = []

        # todo, these time measurements are wrong, since its threaded
        for processed, node in listen.loop():
            processed, data_size, data_time = processed
            if not processed:
                print("Lost connection to node '{}'".format(node))
                nodes[node].close()
                del_list.append(node)
            else:
                sizes.append(data_size)
                times.append(data_time)
                processed_handler(processed, node)

        # print(get_stats.stats)

        for de in del_list:
            del nodes[de]

        if len(nodes.keys()) == 0:
            print("There are no nodes connected to the master, quitting")
            sys.exit(0)

        avg_size = sum(sizes) / len(sizes)
        avg_time = sum(times) / len(times)
        print("The protocol communication recv overhead went at {:.4f}MB/s for {:.4f}s".format(avg_size / avg_time, sum(times)))

    input("Press enter to exit")


def tmp_handler(processed, node):
    print(processed[node][-1], len(processed[node]))


def send_bash_to_nodes(bash):
    scan = scan_ip.scan_ip()
    nodes = scan.scan_space()
    if nodes == {}:
        print("The master could not find any nodes, quitting")
        sys.exit(0)

    send_shit = send_bash.send_bash(nodes)
    send_shit.send_command(bash)

    get_stats = get_statistics_from_nodes.get_statistics_from_nodes(scan.get_secondary_dict())
    get_stats.start_listen()  # use get_stats.stats to get the output of the bash command
    get_stats.wait_for_ans.wait()  # wait for all the nodes to respond

    for node in nodes:
        scan.secondary_node_dict[node].close()
        nodes[node].close()


if __name__ == "__main__":
    send_bash_to_nodes('echo "Hello World"')

    data = None
    try:
        main("find_primes.py", data, util.inf_iter_primes, processed_handler=tmp_handler, start_number=0)
    except KeyboardInterrupt:
        print("Cancelled by user! Bye!")
        sys.exit(0)

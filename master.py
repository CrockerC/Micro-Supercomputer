import net_protocol
import scan_ip
import distribute_data
import handle_stats
import async_listen
import psutil
from multiprocessing.pool import ThreadPool
import functools
import sys
import get_statistics_from_nodes
import send_bash
import processed_handler
import data_generator
import threading
import time
import my_timer

if sys.platform == "win32":
    CPU_COUNT = psutil.cpu_count(logical=False)
elif sys.platform == "linux":
    CPU_COUNT = psutil.cpu_count()
else:
    CPU_COUNT = 4

THREAD_COUNT = CPU_COUNT ** 2


# todo, make better comments before i forget how it all works

# todo, my laptop went to sleep and the master didnt detect it. It also seemed to freeze the whole thing

# todo, implement timestamps and logging for everything
# todo, strftime("[%m/%d/%Y %H:%M:%S]", time.localtime()) gives this [04/02/2021 00:53:24]
# todo, there is also probably a logging library

# todo, make it so that the nodes can kill their job if they lose connection to the master

class master:
    def __init__(self):
        pass

    @staticmethod
    def main_tasking(task, data, data_generator=None, processed_handler=print, handler_args=tuple(), log_path='_sensors_log.csv', **kwargs):
        # parted is how many rounds of processing you want to split your total data into

        scan = scan_ip.scan_ip()
        nodes = scan.scan_space()
        if nodes == {}:
            print("The master could not find any nodes, quitting")
            sys.exit(0)

        print("Connected to", len(nodes), "nodes")

        get_stats = get_statistics_from_nodes.get_statistics_from_nodes(scan.get_secondary_dict())
        get_stats.start_listen()  # use get_stats.stats to get the various stats for all of the nodes
        stat_handler = handle_stats.handle_stats(get_stats, log_path)
        logger = threading.Thread(target=stat_handler.handle, args=tuple())
        logger.start()

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

        pool = ThreadPool()
        for little_data in big_data:
            little_data = distribute_data.distribute_data(len(nodes.keys()), little_data)
            little_data = little_data.split()

            # send each node's data to it synchronously
            # in v2 itll do it asynchronously, although idk how ill handle ordering
            sizes = []

            timer = my_timer.my_timer()
            send_partial = functools.partial(net_protocol.send_task, task_name, task, timer)
            results = list(pool.starmap(send_partial, zip(nodes.values(), list(little_data))))

            start = time.time()
            for result in results:
                data_size = result
                sizes.append(data_size)

            avg_size = sum(sizes) / len(sizes)
            send_time = timer.time() + 0.00000000000001
            print("The protocol communication send overhead went at {:.4f}MB/s for {:.4f}s".format(avg_size / send_time, send_time))
            # free up ram
            del little_data

            del_list = []
            # get the results from each node asynchronously
            # but it also gets them in the same order they were sent out in
            # i know, its trippy lol
            timer = my_timer.my_timer()
            listen = async_listen.multipleListens(nodes.copy(), timer)
            sizes = []

            for processed, node in listen.loop():
                processed, data_size = processed
                if not processed:
                    print("Lost connection to node '{}'".format(node))
                    nodes[node].close()
                    del_list.append(node)
                else:
                    sizes.append(data_size)
                    processed_handler(processed, node, *handler_args)

            print("The nodes spent {:.4f}s processing the data".format(time.time()-start))
            # print(get_stats.stats)

            for de in del_list:
                del nodes[de]

            if len(nodes.keys()) == 0:
                print("There are no nodes connected to the master, quitting")
                sys.exit(0)

            avg_size = sum(sizes) / len(sizes)
            recv_time = timer.time() + 0.00000000000001
            print("The protocol communication recv overhead went at {:.4f}MB/s for {:.4f}s".format(avg_size / recv_time, recv_time))

        input("Press enter to exit")

    @staticmethod
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
    master_node = master()
    # master_node.send_bash_to_nodes('echo "Hello World"')

    try:
        master_node.main_tasking("node_task.py", None, data_generator.data_generator, processed_handler=processed_handler.processed_handler, start_number=2**32)
    except KeyboardInterrupt:
        print("Cancelled by user! Bye!")
        sys.exit(0)

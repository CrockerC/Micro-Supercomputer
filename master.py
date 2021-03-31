import net_protocol
import scan_ip
import test_task
import distribute_data
import util
import async_listen
import inspect


# todo, add ability to measure the out/in speed of the network
# todo, give master a master control over the fans of the nodes
# todo, have nodes report cpu/ram/network/disk usage back to the master
# todo, have master be able to tell the nodes to restart
def main(task, data, parted=1, inf_generator=None, processed_handler=print):
    if parted == 0 and inf_generator is None:
        raise TypeError("If parted is 0, then there must be an inf_iterator")
    ip_scan = scan_ip.scan_ip()
    nodes = ip_scan.scan_space()
    if nodes == {}:
        print("The master could not find any nodes, quitting")
        return

    if parted > 0:
        big_data = distribute_data.distribute_data(parted, data)
        big_data = list(big_data.split())
    else:
        big_data = inf_generator

    task_name = task.__name__
    task = inspect.getsource(task)

    for little_data in big_data:
        little_data = distribute_data.distribute_data(len(nodes.keys()), little_data)
        little_data = little_data.split()

        # send each node's data to it
        for node, datum in zip(nodes, list(little_data)):
            net_protocol.send_task(nodes[node], task, task_name, [datum])

        del_list = []
        # get the results from each node asynchronously
        listen = async_listen.multipleListens(nodes.copy())
        for processed, speed, node in listen.loop():
            if not processed:
                print("Lost connection to node '{}'".format(node))
                nodes[node].close()
                del_list.append(node)
            else:
                res = processed_handler(processed, node)  # ignore this warning
                if res:
                    print(res)

        for de in del_list:
            del nodes[de]

        if len(nodes.keys()) == 0:
            print("There are no nodes connected to the master, quitting")
            return

    input("Press enter to exit")


def tmp_handler(processed, node):
    print(processed[node][-1])


if __name__ == "__main__":
    data = [(i*10000+1, (i+1)*10000) for i in range(10)]
    main(test_task.find_primes, data, 0, util.inf_iter_primes(), processed_handler=tmp_handler)

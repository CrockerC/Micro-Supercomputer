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
# todo, have the nodes and master be able to detect ram usage? this may not be practical
# todo, i could implement a thing that lets it detect when a node is lost and divy up its data to the rest to avoid loss of data
# todo, but idk that seems excessive

# todo, my laptop went to sleep and the master didnt detect it. It also seemed to freeze the whole thing
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

    # todo, i think it would be better to pass a file name and then get the stuff from that.
    task_name = task.__name__
    task = inspect.getsource(task)

    for little_data in big_data:
        little_data = distribute_data.distribute_data(len(nodes.keys()), little_data)
        little_data = little_data.split()

        # send each node's data to it
        for node, datum in zip(nodes, list(little_data)):
            net_protocol.send_task(nodes[node], task, task_name, [datum])

        # free up ram
        del little_data

        del_list = []
        # get the results from each node asynchronously
        # todo, does it really need to be asynchronous????
        # todo, i think yes, if only to make sure that the network buffers stay nice and clear
        # todo, i wonder if i should have it order the data in the async thing, or would it be better to simply hand it off to the handler and let it sort it out
        # todo, cause ram usage could be a concern if the data processing increases the size of the data, but shouldn't that be up to the user to deal with?
        # todo, yeah just add the ordering in the multiple listens. Ram usage is the users problem
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

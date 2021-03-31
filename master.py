import net_protocol
import scan_ip
import test_task
import distribute_data
import util
import async_listen
import inspect


# todo, make better comments before i forget how it all works

# todo, add ability to measure the out/in speed of the network
# todo, give master a master control over the fans of the nodes
# todo, have nodes report cpu/ram/network/disk usage back to the master
# todo, have master be able to tell the nodes to restart
# todo, have the nodes and master be able to detect ram usage? this may not be practical
# todo, implementing all that stuff will require me to either establish multiple connections with each pi
# todo, or create a more detailed network protocol that allows one socket to be used for every utility (which is more expandable, but at the same time much more effort)
# todo, a third option could be to use one socket for the main task, then one for all secondary tasks like ram reporting (which seems to be the best solution)

# todo, give abiliy to install libraries that arent already in the node. This might be somewhat difficult

# todo, i could implement a thing that lets it detect when a node is lost and divy up its data to the rest to avoid loss of data
# todo, but idk that seems like a bit of an edge case, but for very long running tasks like generating primes, something like that could be important

# todo, my laptop went to sleep and the master didnt detect it. It also seemed to freeze the whole thing
def main(task, data, parted=0, data_generator=None, processed_handler=print):
    # parted is how many rounds of processing you want to split your total data into
    # if parted is 0, it uses the data generator you pass it
    if parted == 0 and data_generator is None:
        raise TypeError("If parted is 0, then there must be a data_generator")

    ip_scan = scan_ip.scan_ip()
    nodes = ip_scan.scan_space()
    if nodes == {}:
        print("The master could not find any nodes, quitting")
        return

    if data_generator is None:
        # note that its best to split this so that there are 16 sets of data per pi (cause 4 cores * 4 for mp pool overhead)
        # note but this may differ based on your application and whether you use mp pools or not
        big_data = distribute_data.distribute_data(parted, data)
        big_data = list(big_data.split())
    else:
        big_data = data_generator

    # todo, i think it would be better to pass a file name and then get the stuff from that.
    # todo, so that you dont have to import it, makes it easier to do command line stuff
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
        # but it also gets them in the same order they were sent out in
        # i know, its trippy lol
        listen = async_listen.multipleListens(nodes.copy())
        for processed, speed, node in listen.loop():
            if not processed:
                print("Lost connection to node '{}'".format(node))
                nodes[node].close()
                del_list.append(node)
            else:
                processed_handler(processed, node)  # ignore this warning

        for de in del_list:
            del nodes[de]

        if len(nodes.keys()) == 0:
            print("There are no nodes connected to the master, quitting")
            return

    input("Press enter to exit")


def tmp_handler(processed, node):
    print(processed[node][-1])


if __name__ == "__main__":
    data = None
    main(test_task.find_primes, data, 0, util.inf_iter_primes(), processed_handler=tmp_handler)

import argparse
import master
import data_generator
import processed_handler


# todo, doing keyboard interrupt doesnt work right
if __name__ == '__main__':
    argparser = argparse.ArgumentParser(
        description='Micro-Supercomputer master control')
    argparser.add_argument(
        '-b', '--bash',
        default=None,
        help='execute command in shell of nodes')
    argparser.add_argument(
        '-t', '--task',
        default=None,
        help='path of the task file')

    master_node = master.master()

    args = argparser.parse_args()
    if args.bash:
        master_node.send_bash_to_nodes(args.bash)
    elif args.task:
        master_node.main_tasking(args.task, None, data_generator.data_generator, processed_handler.processed_handler)
    else:
        print("Need to give the master something to do")

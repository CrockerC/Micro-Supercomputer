import socket
import threading
import ipaddress
import net_protocol
import time
import random


class scan_ip:
    def __init__(self, ip_radius=4001, primary_port=12321, secondary_port=12322):
        self.__primary_port = primary_port
        self.__secondary_port = secondary_port
        self.__ip_radius = ip_radius
        self.__num_scan_threads = 500
        self.__call = bytes("x gon", 'utf-8')
        self.__response = bytes("give it to ya", 'utf-8')

        self.ip_address = net_protocol.get_ip()
        self.ip_range = tuple()
        self.__ip_type = str()
        self.__ip_space_size = int()
        self.primary_node_dict = dict()  # format of {'[ip]': socket}
        self.secondary_node_dict = dict()  # format of {'[ip]': socket}

        self.__get_lan_type()

    def get_primary_dict(self):
        return self.primary_node_dict

    def get_secondary_dict(self):
        return self.secondary_node_dict

    def __get_socket(self):
        start_port = 10000
        end_port = 60000
        s = None
        timeout = 30
        start = time.time()
        # doing this with random numbers makes it faster than being procedural
        # like, a lot faster
        while time.time() - start < timeout:
            port = random.randint(start_port, end_port)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(.01)
                
                s.bind((self.ip_address, port))
                s.settimeout(None)
                return s
            except Exception as e:
                if e is KeyboardInterrupt:
                    raise KeyboardInterrupt
                if s:
                    s.close()
            port += 1
        return None

    def __get_lan_type(self):
        # i discovered that when using a vpn this doesnt work very well....
 
        start = ipaddress.ip_address(self.ip_address) - self.__ip_radius
        end = ipaddress.ip_address(self.ip_address) + self.__ip_radius

        self.__ip_type = self.ip_address.split('.')[0]
        if self.__ip_type == '10':
            # i know that this and the 172 have the same code, its left like that in case i want to change it in the future
            self.ip_range = (str(start), str(end))
            self.__ip_space_size = int(end) - int(start) + 1
        elif self.__ip_type == '172':
            self.ip_range = (str(start), str(end))
            self.__ip_space_size = int(end) - int(start) + 1
        elif self.__ip_type == '192':
            # don't bother with the truncating when there are only 65k addresses
            self.ip_range = ('192.168.0.0', '192.168.255.255')
            self.__ip_space_size = 65536
        elif self.__ip_type == '169':
            self.ip_range = ('169.254.1.0', '169.254.254.255')
            self.__ip_space_size = int(ipaddress.ip_address('169.254.254.255')) - int(ipaddress.ip_address('169.254.1.0')) 

        else:
            raise ValueError("LAN address space not found!")

    @staticmethod
    def __ip_range_generator(start, stop):
        curr = ipaddress.ip_address(start)
        end = ipaddress.ip_address(stop)
        while int(curr) <= int(end):
            curr += 1
            yield str(curr)

    # todo, find a better way to chose the scanned space
    def scan_space(self):
        num_addresses_per_thread = self.__ip_space_size // self.__num_scan_threads
        extra_addresses = self.__ip_space_size % self.__num_scan_threads
        end = 0

        # scan through the ip space not including the extra addresses at the end
        threads = []
        for i in range(self.__num_scan_threads):
            if i == self.__num_scan_threads-1:
                start = end + 1
                end = start + extra_addresses - 1
                ip_range = (str(start), str(end))
                thread = threading.Thread(target=self.__scan_thread, args=(ip_range,))
                threads.append(thread)

            start = ipaddress.ip_address(self.ip_range[0]) + i * num_addresses_per_thread
            end = ipaddress.ip_address(self.ip_range[0]) + (i+1) * num_addresses_per_thread - 1
            ip_range = (str(start), str(end))
            thread = threading.Thread(target=self.__scan_thread, args=(ip_range,))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        return self.get_primary_dict()

    def __scan_thread(self, ip_range):
        ip_range = self.__ip_range_generator(*ip_range)
        for ip in ip_range:
            s = self.__get_socket()
            s.settimeout(.1)
            try:
                s.connect((ip, self.__primary_port))
                try:
                    net_protocol.sendall(s, self.__call)
                    response = net_protocol.recv_data(s)
                except socket.timeout:
                    raise ValueError("No response from node! Not adding to list!")
                if response == self.__response:
                    self.primary_node_dict.update({ip: s})

                    s = self.__get_socket()
                    s.settimeout(.1)
                    s.connect((ip, self.__secondary_port))

                    self.secondary_node_dict.update({ip: s})
                    print("Connected to node {}".format(ip))
                else:
                    raise ValueError("Wrong response from node! Not adding to list!, response was", response)
            except socket.timeout:
                s.close()
            except OSError as err:
                print((ip, self.__primary_port), err)


if __name__ == "__main__":
    tmp = scan_ip()
    print(tmp.scan_space())
    input("Press enter to exit")

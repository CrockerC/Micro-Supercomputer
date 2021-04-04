import time
import threading
import orjson as json


with open("test.txt", "r") as f:
    data = f.read()
    data *= 5


def json_thread_test(data):
    num_threads = 10

    # st compress
    start = time.time()
    for i in range(num_threads):
        serialized_data = json.dumps(data)
    tt1 = time.time() - start

    # st decompress
    start = time.time()
    for i in range(num_threads):
        json.loads(serialized_data)
    tt3 = time.time() - start

    # mt compress
    start = time.time()
    threads = []
    for i in range(num_threads):
        tmp = threading.Thread(target=json.dumps, args=(data,))
        tmp.start()
        threads.append(tmp)

    for thread in threads:
        thread.join()
    tt2 = time.time() - start

    # mt decompress
    start = time.time()
    threads = []
    for i in range(num_threads):
        tmp = threading.Thread(target=json.loads, args=(serialized_data,))
        tmp.start()
        threads.append(tmp)

    for thread in threads:
        thread.join()
    tt4 = time.time() - start

    print("Mp Compression time:", tt2)
    print("Mp Decompression time:", tt4)
    print("Compression ratio:", len(data) / len(serialized_data))
    print("Mp ratio is:", tt1 / tt2)


print("running mp json test")
json_thread_test(data)
print()

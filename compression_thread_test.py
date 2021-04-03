import time
import threading
import brotli
import gzip
import lz4.frame
import zstd

with open("test.txt", "rb") as f:
    data = f.read()
    data *= 5


def compression_thread_test(algo, args):
    num_threads = 10

    # st compress
    start = time.time()
    for i in range(num_threads):
        comp_data = algo.compress(*args)
    tt1 = time.time() - start

    # st decompress
    start = time.time()
    for i in range(num_threads):
        algo.decompress(comp_data)
    tt3 = time.time() - start

    # mt compress
    start = time.time()
    threads = []
    for i in range(num_threads):
        tmp = threading.Thread(target=algo.compress, args=args)
        tmp.start()
        threads.append(tmp)

    for thread in threads:
        thread.join()
    tt2 = time.time() - start

    # mt decompress
    start = time.time()
    threads = []
    for i in range(num_threads):
        tmp = threading.Thread(target=algo.decompress, args=(comp_data,))
        tmp.start()
        threads.append(tmp)

    for thread in threads:
        thread.join()
    tt4 = time.time() - start

    print("Mp Compression time:", tt2)
    print("Mp Decompression time:", tt4)
    print("Compression ratio:", len(data) / len(comp_data))
    print("Mp ratio is:", tt1 / tt2)


print("lz4 mp test")
compression_thread_test(lz4.frame, (data, lz4.frame.COMPRESSIONLEVEL_MINHC))
print()
print("brotli mp test")
compression_thread_test(brotli, (data, brotli.MODE_GENERIC, 1))
print()
print("zstd mp test")
compression_thread_test(zstd, (data, 1))

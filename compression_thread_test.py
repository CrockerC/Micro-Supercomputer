import time
import threading
import brotli

data = b"This is a test string" * 500000000

num_threads = 10
start = time.time()
for i in range(num_threads):
    comp_data = brotli.compress(data, quality=1)
tt1 = time.time()-start

start = time.time()
threads = []
for i in range(num_threads):
    tmp = threading.Thread(target=brotli.compress, args=(data, brotli.MODE_GENERIC, 1))
    tmp.start()
    threads.append(tmp)

for i in range(num_threads):
    threads[i].join()
tt2 = time.time()-start

print("Mp ratio is:", tt1/tt2)
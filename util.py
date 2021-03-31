

def inf_iter_primes(num_per_iter=64, range_size=10000):
    i = 0
    # note that this is not maxing out the cpu on my desktop, so make sure that it does on the pis
    # also note that increasing the size of the range increases the ram usage
    while True:
        yield [(i*range_size+1, (i+1)*range_size) for i in range(i, i+num_per_iter)]
        i += num_per_iter


if __name__ == "__main__":
    # just making sure that the number of numbers doesnt change every loop
    # for you know, ram
    for thing in inf_iter_primes(4):
        print(thing[0][1] - thing[0][0])

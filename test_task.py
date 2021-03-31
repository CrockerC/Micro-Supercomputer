import time
import numpy as np
import pathos.multiprocessing as mp
import sympy
import inflect

# todo, https://pypi.org/project/miller-rabin/
# todo, this library seems to not work for windows
# todo, but it claims to be about 30x faster than my current thing
# todo, so when i get this on the pi. Lets give it a try


class find_primes_py_st:
    def __init__(self, ranges):
        self.ranges = ranges

    def run(self):
        import numpy
        # Record the test start time
        foo = numpy.vectorize(self.is_prime)

        all_primes = []
        for start, stop in self.ranges:
            nums = numpy.arange(start, stop)
            pbools = foo(nums)
            primes = numpy.extract(pbools, nums)
            all_primes += list(primes)

        # Display the results, uncomment the last to list the prime numbers found
        # print('Find all primes up to: ' + str(self.end_number))
        # print('Time elasped: ' + str(end) + ' seconds')
        print('Number of primes found ' + str(len(all_primes)))
        return all_primes

    def is_prime(self, n):
        import numpy
        if n % 2 == 0 and n > 2:
            return False
        return all(n % i for i in range(3, int(numpy.sqrt(n)) + 1, 2))


class find_primes_py:
    def __init__(self, ranges):
        self.ranges = ranges
        self.foo = None

    def run(self):
        # Record the test start time
        self.foo = np.vectorize(self.is_prime)

        all_primes = []
        pool = mp.ProcessPool()
        results = pool.map(self.multi_pro, self.ranges)

        for res in results:
            all_primes += res

        print('Number of primes found ' + str(len(all_primes)))
        return all_primes

    def multi_pro(self, range_):
        start, stop = range_
        nums = np.arange(start, stop)
        pbools = self.foo(nums)
        primes = np.extract(pbools, nums)
        return list(primes)

    @staticmethod
    def is_prime(n):
        if n % 2 == 0 and n > 2:
            return False
        return all(n % i for i in range(3, int(np.sqrt(n)) + 1, 2))


class find_primes:
    def __init__(self, ranges):
        self.ranges = ranges
        self.foo = None

    def run(self):
        # Record the test start time
        self.foo = np.vectorize(self.is_prime)

        all_primes = []
        pool = mp.ProcessPool()
        results = pool.map(self.multi_pro, self.ranges)

        for res in results:
            all_primes += res

        print('Number of primes found ' + str(len(all_primes)))
        return all_primes

    def multi_pro(self, range_):
        start, stop = range_
        nums = np.arange(start, stop)
        pbools = self.foo(nums)
        primes = np.extract(pbools, nums)
        return list(primes)

    @staticmethod
    def is_prime(n):
        # note that this method is only deterministic for numbers less than 2^64, above that it may be required to have a deterministic formula double check them
        return sympy.isprime(n)


class find_primes_st:
    def __init__(self, ranges):
        self.ranges = ranges

    def run(self):
        import numpy
        # Record the test start time
        foo = numpy.vectorize(self.is_prime)
        start = time.time()

        all_primes = []
        for start, stop in self.ranges:
            nums = numpy.arange(start, stop)
            pbools = foo(nums)
            primes = numpy.extract(pbools, nums)
            all_primes += list(primes)

        # Display the results, uncomment the last to list the prime numbers found
        # print('Find all primes up to: ' + str(self.end_number))
        # print('Time elasped: ' + str(end) + ' seconds')
        print('Number of primes found ' + str(len(all_primes)))
        return all_primes

    @staticmethod
    def is_prime(n):
        return sympy.isprime(n)


if __name__ == "__main__":
    range_test = (10000000000, 10000010000)
    test_ranges = [range_test] * (8 * 8)
    precision = 4
    p = inflect.engine()
    print("Calculating primes in the range:\n'{}' \nto \n'{}'".format(p.number_to_words(range_test[0]), p.number_to_words(range_test[1])))

    # run the mp py method
    print("\nCalculating with the multiprocesed py method")
    start = time.time()
    primes = find_primes_py(test_ranges)
    primes.run()
    total = time.time() - start
    print("It took {}s, which is {}s per 'thread'".format(round(total, precision), round(total / len(test_ranges), precision)))

    print("\nCalculating with the py method")
    # run the sp py method
    start = time.time()
    primes = find_primes_py_st([range_test])
    primes.run()
    single_time = time.time() - start
    print("It took {}s".format(round(single_time, precision)))

    print("\nCalculating with the sy method")
    # run the sp sy method
    start = time.time()
    primes = find_primes_st([range_test])
    primes.run()
    sy_single_time = time.time() - start
    print("It took {}s".format(round(sy_single_time, precision)))

    print("\nCalculating with the multiprocesed sy method")
    # run the mp sy method
    start = time.time()
    primes = find_primes(test_ranges)
    primes.run()
    sy_total = time.time() - start
    print("It took {}s, which is {}s per 'thread'\n".format(round(sy_total, precision), round(sy_total / len(test_ranges), precision)))

    sy_average = sy_total / len(test_ranges)
    mp_ratio_sy = round(sy_single_time / sy_average, precision)
    # print("the single threaded method time was {}s, the average time for the multithreaded method was {}s".format(round(sy_single_time, 3), round(sy_total / len(ranges), 3)))
    print("The mp ratio for the sy method with {} 'threads' is {}\n".format(len(test_ranges), mp_ratio_sy))

    avg_time = total / len(test_ranges)
    mp_ratio = round(single_time / avg_time, precision)
    # print("the single threaded method time was {}s, the average time for the multithreaded method was {}s".format(round(single_time, 3), round(avg_time, 3)))
    print("The mp ratio with for the py {} 'threads' is {}\n".format(len(test_ranges), mp_ratio))

    print("Dispite the mp ratio of the sy method being only {}% of the py method, the sy multicore method was {}x faster than the py multicore".format(round(mp_ratio_sy / mp_ratio*100, precision), round(total / sy_total, precision)))

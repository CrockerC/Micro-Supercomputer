
class node_task:
    # note, no importing mod.attr
    # for example pathos.multiprocessing will not work!
    mp = __import__('pathos')
    np = __import__('numpy')
    sympy = __import__('sympy')

    def __init__(self, ranges):
        self.ranges = ranges
        self.foo = None

    def run(self):
        # Record the test start time
        self.foo = self.np.vectorize(self.is_prime)

        all_primes = []
        pool = self.mp.multiprocessing.ProcessPool()
        results = pool.map(self.multi_pro, self.ranges)

        for res in results:
            all_primes += res

        return all_primes

    def multi_pro(self, range_):
        start, stop = range_
        nums = list(range(start, stop))
        pbools = self.foo(nums)
        primes = [num for num, boo in zip(nums, pbools) if boo]
        return primes

    def is_prime(self, n):
        # note that this method is only deterministic for numbers less than 2^64, above that it may be required to have a deterministic formula double check them
        return self.sympy.isprime(n)

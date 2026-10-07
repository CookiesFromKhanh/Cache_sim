"""Simple cache simulator: CPU <-> Cache <-> DRAM (write-through).

Task 3: direct-mapped cache, 16 blocks, block size 1, 6-bit addresses.
Task 4: 2-way set associative cache with LRU replacement.
"""
import random


def to_bin(addr):
    return bin(addr)[2:].zfill(6)          # e.g. 52 -> '110100'


# ---------------------------------------------------------------- DRAM
class DRAM:
    def __init__(self):
        random.seed(1)
        self.cells = []                    # 8 rows x 8 columns
        for row in range(8):
            one_row = []
            for col in range(8):
                one_row.append(random.randint(0, 99))
            self.cells.append(one_row)

    def read(self, addr):
        row = addr // 8                    # top 3 bits of the address
        col = addr % 8                     # bottom 3 bits
        return self.cells[row][col]

    def write(self, addr, value):
        row = addr // 8
        col = addr % 8
        self.cells[row][col] = value


# ------------------------------------------- Task 3: direct-mapped cache
class DirectMappedCache:
    def __init__(self, dram):
        self.dram = dram
        self.hits = 0
        self.misses = 0
        # 16 blocks -> 4 index bits, 6 - 4 = 2 tag bits
        self.tag = [0] * 16                # tag store
        self.valid = [0] * 16              # valid bits
        self.data = [0] * 16               # data store

    def access(self, rw, addr, value=None):
        index = addr % 16                  # which cache block (low 4 bits)
        tag = addr // 16                   # remaining high 2 bits
        hit = (self.valid[index] == 1 and self.tag[index] == tag)

        if hit:
            self.hits += 1
            print(hex(addr), to_bin(addr), "HIT")
            if rw == 0:
                return self.data[index]    # read: send data to CPU
            self.data[index] = value       # write: update cache copy
            self.dram.write(addr, value)   # write-through to DRAM
            return None

        self.misses += 1
        print(hex(addr), to_bin(addr), "MISS")
        if rw == 1:                        # write miss: only write DRAM
            self.dram.write(addr, value)
            return None

        data = self.dram.read(addr)        # read miss: fetch from DRAM
        self.tag[index] = tag              # update tag, valid, data
        self.valid[index] = 1
        self.data[index] = data
        return data


# ----------------------------------- Task 4: 2-way cache with LRU policy
class LRUCache:
    def __init__(self, dram):
        self.dram = dram
        self.hits = 0
        self.misses = 0
        # 16 blocks / 2 ways = 8 sets -> 3 index bits, 3 tag bits.
        # Each set is a list of [tag, data] entries. A block is in the list
        # only if it is valid. Order: first = least recently used,
        # last = most recently used.
        self.sets = []
        for i in range(8):
            self.sets.append([])

    def access(self, rw, addr, value=None):
        index = addr % 8                   # which set
        tag = addr // 8
        the_set = self.sets[index]

        # look for the block in this set
        found = None
        for entry in the_set:
            if entry[0] == tag:
                found = entry

        if found is not None:
            self.hits += 1
            print(hex(addr), to_bin(addr), "HIT")
            the_set.remove(found)          # move to the end = most recent
            the_set.append(found)
            if rw == 0:
                return found[1]
            found[1] = value
            self.dram.write(addr, value)
            return None

        self.misses += 1
        print(hex(addr), to_bin(addr), "MISS")
        if rw == 1:
            self.dram.write(addr, value)
            return None

        data = self.dram.read(addr)
        if len(the_set) == 2:              # set full: evict least recently used
            evicted = the_set.pop(0)
            print("   evicted block with tag", evicted[0])
        the_set.append([tag, data])
        return data


# -------------------------------------------------------------- main
def run(name, cache, requests):
    print("\n=====", name, "=====")
    for rw, addr, value in requests:
        result = cache.access(rw, addr, value)
        if rw == 0:
            print("   data to CPU:", result)
    total = cache.hits + cache.misses
    print("hits:", cache.hits, " misses:", cache.misses,
          " hit rate:", round(100 * cache.hits / total, 1), "%")


# each request: (0 = read / 1 = write, address, data to write)
requests = [
    (0, 0x34, None), (0, 0x18, None), (0, 0x36, None), (0, 0x34, None),
    (0, 0x14, None), (1, 0x34, 77),   (0, 0x34, None), (0, 0x04, None),
    (1, 0x05, 55),   (0, 0x05, None), (0, 0x24, None), (0, 0x04, None),
    (0, 0x14, None), (0, 0x24, None), (0, 0x04, None), (0, 0x14, None),
]

run("Task 3: direct-mapped", DirectMappedCache(DRAM()), requests)
run("Task 4: 2-way LRU", LRUCache(DRAM()), requests)

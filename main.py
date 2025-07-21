import sys
import struct
import random
from collections import deque

class Cache:
    def __init__(self, nsets, bsize, assoc, subst):
        self.nsets = nsets
        self.bsize = bsize
        self.assoc = assoc
        self.subst = subst.upper()
        self.cache = [[] for _ in range(nsets)]  # Each set contains a list of (tag, valid, age/timestamp) tuples
        self.total_accesses = 0
        self.hits = 0
        self.misses = 0
        self.compulsory_misses = 0
        self.capacity_misses = 0
        self.conflict_misses = 0
        self.seen_tags = set()  # To track unique tags for compulsory misses
        self.address_bits = 32
        self.calculate_address_fields()

    def calculate_address_fields(self):
        """Calculate the number of bits for offset, index, and tag."""
        self.offset_bits = self.log2(self.bsize)
        self.index_bits = self.log2(self.nsets)
        self.tag_bits = self.address_bits - self.offset_bits - self.index_bits

    def log2(self, x):
        """Calculate the base-2 logarithm of x."""
        return (x - 1).bit_length()

    def get_address_components(self, address):
        """Extract tag and index from the 32-bit address."""
        offset_mask = (1 << self.offset_bits) - 1
        index_mask = (1 << self.index_bits) - 1
        index = (address >> self.offset_bits) & index_mask
        tag = address >> (self.offset_bits + self.index_bits)
        return tag, index

    def access_cache(self, address):
        """Simulate a cache access for the given address."""
        self.total_accesses += 1
        tag, index = self.get_address_components(address)
        set_content = self.cache[index]

        # Check for hit
        for entry in set_content:
            if entry[0] == tag and entry[1]:  # Valid entry with matching tag
                self.hits += 1
                if self.subst == 'L':  # Update LRU timestamp
                    entry[2] = self.total_accesses
                elif self.subst == 'F':  # Move to end for FIFO
                    set_content.remove(entry)
                    set_content.append(entry)
                return

        # Miss handling
        self.misses += 1
        is_compulsory = (tag, index) not in self.seen_tags
        self.seen_tags.add((tag, index))

        # Check if set is full
        set_full = len(set_content) >= self.assoc
        cache_full = sum(len(s) for s in self.cache) >= self.nsets * self.assoc

        # Classify miss
        if is_compulsory:
            self.compulsory_misses += 1
        elif set_full and cache_full:
            self.capacity_misses += 1
        elif set_full:
            self.conflict_misses += 1
        else:
            self.compulsory_misses += 1  # Treat as compulsory if not full

        # Add new entry
        new_entry = [tag, True, self.total_accesses]  # [tag, valid, timestamp/age]
        if not set_full:
            set_content.append(new_entry)
        else:
            # Replace an entry based on substitution policy
            if self.subst == 'R':
                idx = random.randint(0, self.assoc - 1)
                set_content[idx] = new_entry
            elif self.subst == 'F':
                set_content.pop(0)  # Remove oldest
                set_content.append(new_entry)
            elif self.subst == 'L':
                # Find least recently used (smallest timestamp)
                lru_idx = 0
                min_time = set_content[0][2]
                for i, entry in enumerate(set_content[1:], 1):
                    if entry[2] < min_time:
                        min_time = entry[2]
                        lru_idx = i
                set_content[lru_idx] = new_entry

    def print_stats(self, flag_out):
        """Print statistics based on the output flag."""
        hit_rate = self.hits / self.total_accesses if self.total_accesses > 0 else 0
        miss_rate = self.misses / self.total_accesses if self.total_accesses > 0 else 0
        compulsory_rate = self.compulsory_misses / self.misses if self.misses > 0 else 0
        capacity_rate = self.capacity_misses / self.misses if self.misses > 0 else 0
        conflict_rate = self.conflict_misses / self.misses if self.misses > 0 else 0

        if flag_out == 0:
            print(f"Total de acessos: {self.total_accesses}")
            print(f"Taxa de hits: {hit_rate:.4f}")
            print(f"Taxa de misses: {miss_rate:.4f}")
            print(f"Taxa de miss compulsório: {compulsory_rate:.4f}")
            print(f"Taxa de miss de capacidade: {capacity_rate:.4f}")
            print(f"Taxa de miss de conflito: {conflict_rate:.4f}")
        else:
            print(f"{self.total_accesses} {hit_rate:.4f} {miss_rate:.4f} "
                  f"{compulsory_rate:.4f} {capacity_rate:.4f} {conflict_rate:.4f}")

def main():
    if len(sys.argv) != 7:
        print("Uso: python cache_simulator.py <nsets> <bsize> <assoc> <substituição> <flag_saida> arquivo_de_entrada")
        sys.exit(1)

    try:
        nsets = int(sys.argv[1])
        bsize = int(sys.argv[2])
        assoc = int(sys.argv[3])
        subst = sys.argv[4].upper()
        flag_out = int(sys.argv[5])
        input_file = sys.argv[6]
    except ValueError:
        print("Erro: Parâmetros numéricos inválidos.")
        sys.exit(1)

    # Validate parameters
    if nsets <= 0 or bsize <= 0 or assoc <= 0:
        print("Erro: nsets, bsize e assoc devem ser maiores que zero.")
        sys.exit(1)
    if subst not in ['R', 'F', 'L']:
        print("Erro: Política de substituição deve ser 'R', 'F' ou 'L'.")
        sys.exit(1)
    if flag_out not in [0, 1]:
        print("Erro: flag_saida deve ser 0 ou 1.")
        sys.exit(1)

    # Initialize cache
    cache = Cache(nsets, bsize, assoc, subst)

    # Read input file
    try:
        with open(input_file, 'rb') as f:
            while True:
                # Read 4 bytes (32-bit address) in big-endian
                data = f.read(4)
                if not data:
                    break
                address = struct.unpack('>I', data)[0]
                cache.access_cache(address)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{input_file}' não encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        sys.exit(1)

    # Print results
    cache.print_stats(flag_out)

if __name__ == '__main__':
    main()
import ctypes
from ctypes import c_uint64, c_uint32, c_double, POINTER
import math

class IntelHardwareRNG:
    def __init__(self, library_path='./rdrand.so'):
        """
        Initialize Intel Hardware RNG wrapper

        Args:
            library_path: Path to compiled shared library (.so on Linux, .dll on Windows)
        """
        try:
            self.lib = ctypes.CDLL(library_path)
        except OSError as e:
            raise RuntimeError(f"Failed to load library {library_path}: {e}")

        # Define function signatures for basic functions
        self.lib.get_bits_using_rdrand.restype = c_uint64
        self.lib.get_bits_using_rdseed.restype = c_uint64
        self.lib.RdRand_cpuid.restype = ctypes.c_int
        self.lib.RdSeed_cpuid.restype = ctypes.c_int

        # Define signatures for range functions
        self.lib.rdrand_range.argtypes = [c_uint64, c_uint64]
        self.lib.rdrand_range.restype = c_uint64
        self.lib.rdseed_range.argtypes = [c_uint64, c_uint64]
        self.lib.rdseed_range.restype = c_uint64

        # Define signatures for double functions
        self.lib.rdrand_double.restype = c_double
        self.lib.rdseed_double.restype = c_double
        self.lib.rdrand_double_range.argtypes = [c_double, c_double]
        self.lib.rdrand_double_range.restype = c_double
        self.lib.rdseed_double_range.argtypes = [c_double, c_double]
        self.lib.rdseed_double_range.restype = c_double

        # Define signatures for byte functions
        self.lib.rdrand_bytes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), c_uint32]
        self.lib.rdseed_bytes.argtypes = [ctypes.POINTER(ctypes.c_ubyte), c_uint32]

        # Check hardware support
        self.has_rdrand = bool(self.lib.RdRand_cpuid())
        self.has_rdseed = bool(self.lib.RdSeed_cpuid())

        if not self.has_rdrand:
            raise RuntimeError("CPU does not support RDRAND instruction")

        print(f"Hardware Support - RDRAND: {self.has_rdrand}, RDSEED: {self.has_rdseed}")

    def rdrand_64(self):
        """Get 64-bit random number using RDRAND"""
        if not self.has_rdrand:
            raise RuntimeError("RDRAND not supported")
        return self.lib.get_bits_using_rdrand()

    def rdseed_64(self):
        """Get 64-bit random number using RDSEED"""
        if not self.has_rdseed:
            raise RuntimeError("RDSEED not supported")
        return self.lib.get_bits_using_rdseed()

    def random_range(self, min_val, max_val, use_rdseed=False):
        """
        Generate random number in specified range (uses C implementation)

        Args:
            min_val: Minimum value (inclusive)
            max_val: Maximum value (inclusive)
            use_rdseed: If True, use RDSEED; otherwise use RDRAND

        Returns:
            Random number in [min_val, max_val]
        """
        if min_val > max_val:
            raise ValueError("min_val must be <= max_val")

        if use_rdseed:
            if not self.has_rdseed:
                raise RuntimeError("RDSEED not supported")
            return self.lib.rdseed_range(min_val, max_val)
        else:
            return self.lib.rdrand_range(min_val, max_val)

    def random_float(self, min_val=0.0, max_val=1.0, use_rdseed=False):
        """
        Generate random float in specified range (uses C implementation)

        Args:
            min_val: Minimum value
            max_val: Maximum value
            use_rdseed: If True, use RDSEED; otherwise use RDRAND

        Returns:
            Random float in [min_val, max_val)
        """
        if use_rdseed:
            if not self.has_rdseed:
                raise RuntimeError("RDSEED not supported")
            return self.lib.rdseed_double_range(min_val, max_val)
        else:
            return self.lib.rdrand_double_range(min_val, max_val)

    def random_bytes(self, length, use_rdseed=False):
        """
        Generate random bytes (uses C implementation)

        Args:
            length: Number of bytes to generate
            use_rdseed: If True, use RDSEED; otherwise use RDRAND

        Returns:
            bytes object of specified length
        """
        if length <= 0:
            raise ValueError("Length must be positive")

        # Create buffer
        buffer = (ctypes.c_ubyte * length)()

        if use_rdseed:
            if not self.has_rdseed:
                raise RuntimeError("RDSEED not supported")
            self.lib.rdseed_bytes(buffer, length)
        else:
            self.lib.rdrand_bytes(buffer, length)

        # Convert to bytes
        return bytes(buffer)

    def random_choice(self, sequence, use_rdseed=False):
        """
        Choose random element from sequence

        Args:
            sequence: List, tuple, or other sequence
            use_rdseed: If True, use RDSEED; otherwise use RDRAND

        Returns:
            Random element from sequence
        """
        if not sequence:
            raise ValueError("Cannot choose from empty sequence")

        index = self.random_range(0, len(sequence) - 1, use_rdseed)
        return sequence[index]


# Example usage
if __name__ == "__main__":
    try:
        # Initialize the RNG (you'll need to compile the C code first)
        rng = IntelHardwareRNG('./rdrand.so')

        # Generate numbers in your specified range
        min_val = 100000000000000
        max_val = 999999999999999

        print("Using RDRAND:")
        for i in range(5):
            num = rng.random_range(min_val, max_val, use_rdseed=False)
            print(f"Random number {i+1}: {num}")

        if rng.has_rdseed:
            print("\nUsing RDSEED:")
            for i in range(5):
                num = rng.random_range(min_val, max_val, use_rdseed=True)
                print(f"Random number {i+1}: {num}")

        # Generate random floats
        print("\nRandom floats between 0.5 and 1.5:")
        for i in range(3):
            float_val = rng.random_float(0.5, 1.5)
            print(f"Float {i+1}: {float_val}")

        # Generate random bytes
        random_data = rng.random_bytes(16)
        print(f"\nRandom bytes: {random_data.hex()}")

        # Random choice
        choices = ['apple', 'banana', 'cherry', 'date', 'elderberry']
        choice = rng.random_choice(choices)
        print(f"Random choice: {choice}")

    except RuntimeError as e:
        print(f"Error: {e}")
        print("Note: You need to compile the C code into a shared library first")
        print("Example: gcc -shared -fPIC -o rdrand.so rdrand.c")

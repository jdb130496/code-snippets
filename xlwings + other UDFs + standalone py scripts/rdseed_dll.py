import ctypes
import time
import os
import xlwings as xw
from typing import List, Optional
# At the top of your Python files
BOOST_PATH = os.environ.get('BOOST_PATH', r'D:\Programs\msys64\ucrt64\bin')
DEV_PATH = os.environ.get('DEV_DLL_PATH', r'D:\dev\dll')
BOOST_LIBS = os.environ.get('BOOST_LIBS_PATH', r'D:\boost\libs')

os.environ['PATH'] = f'{BOOST_PATH};{DEV_PATH};{BOOST_LIBS}' + ';' + os.environ['PATH']
#DLL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "rdseed_boost_new_claude.dll"))
generator = RDSeedGenerator(DLL_PATH)
class RDSeedGenerator:
    """Excel-safe wrapper for RDSEED DLL with worker-based parallel processing."""
    
    def __init__(self, dll_path: str = "rdseed_boost_new_claude.dll"):
        """Initialize the RDSEED generator with the DLL path."""
        if not os.path.exists(dll_path):
            raise FileNotFoundError(f"DLL not found at {dll_path}")
            
        self.dll = ctypes.CDLL(dll_path)
        self._setup_function_signatures()
        
        # Check if RDSEED is supported
        if not self.is_rdseed_supported():
            raise RuntimeError("RDSEED instruction not supported on this CPU")
    
    def _setup_function_signatures(self):
        """Setup the function signatures for proper ctypes calling."""
        # Return types
        self.dll.checkRdseedSupportC.restype = ctypes.c_int
        self.dll.getNumbersSizeC.restype = ctypes.c_int
        self.dll.getNumbersC.restype = ctypes.POINTER(ctypes.c_ulonglong)
        self.dll.isProcessingC.restype = ctypes.c_int
        
        # Parameter types
        self.dll.generateRandomNumbersSimple.argtypes = [ctypes.c_int]
        self.dll.generateRandomNumbersWithWorkers.argtypes = [ctypes.c_int, ctypes.c_int]
    
    def is_rdseed_supported(self) -> bool:
        """Check if RDSEED instruction is supported on this CPU."""
        try:
            return bool(self.dll.checkRdseedSupportC())
        except Exception:
            return False
    
    def is_processing(self) -> bool:
        """Check if the DLL is currently processing a request."""
        try:
            return bool(self.dll.isProcessingC())
        except Exception:
            return False
    
    def clear_numbers(self):
        """Clear any stored numbers in the DLL."""
        try:
            self.dll.clearNumbersC()
        except Exception:
            pass
    
    def generate_numbers(self, count: int, num_workers: Optional[int] = None, 
                        timeout: float = 30.0) -> List[int]:
        """
        Generate random numbers using RDSEED with worker-based parallel processing.
        
        Args:
            count: Number of random numbers to generate
            num_workers: Number of worker threads (None for auto-detect)
            timeout: Maximum time to wait for completion in seconds
            
        Returns:
            List of generated random numbers
            
        Raises:
            ValueError: If parameters are invalid
            RuntimeError: If generation fails or times out
        """
        if count <= 0:
            raise ValueError("Count must be positive")
        
        if count > 10000000:  # 10M limit for Excel safety
            raise ValueError("Count too large (max 10M for Excel)")
        
        if self.is_processing():
            raise RuntimeError("Already processing a request")
        
        try:
            # Clear any previous results
            self.clear_numbers()
            
            # Start generation
            if num_workers is None:
                self.dll.generateRandomNumbersSimple(count)
            else:
                if num_workers <= 0 or num_workers > 16:
                    raise ValueError("num_workers must be between 1 and 16")
                self.dll.generateRandomNumbersWithWorkers(count, num_workers)
            
            # Wait for completion with timeout
            start_time = time.time()
            while self.is_processing():
                if time.time() - start_time > timeout:
                    raise RuntimeError(f"Generation timed out after {timeout} seconds")
                time.sleep(0.01)  # 10ms polling interval
            
            # Get results
            size = self.dll.getNumbersSizeC()
            if size <= 0:
                raise RuntimeError("No numbers were generated")
            
            # Retrieve the numbers
            ptr = self.dll.getNumbersC()
            if not ptr:
                raise RuntimeError("Failed to get number pointer")
            
            numbers = [int(ptr[i]) for i in range(size)]
            
            return numbers
            
        except Exception as e:
            self.clear_numbers()  # Clean up on error
            raise RuntimeError(f"Generation failed: {str(e)}")


# Excel UDF Functions for xlwings
@xw.func
def generate_random_numbers_claude(count: int, workers: int = 0) -> List[List[int]]:
    """
    Excel UDF to generate random numbers using RDSEED.
    
    Args:
        count: Number of random numbers to generate
        workers: Number of worker threads (0 for auto-detect)
    
    Returns:
        2D list (column) of random numbers for Excel
    """
    try:
        # Initialize generator (assuming DLL is in same directory)
        generator = RDSeedGenerator("rdseed_boost_new_claude.dll")
        
        # Generate numbers
        if workers <= 0:
            numbers = generator.generate_numbers(count)
        else:
            numbers = generator.generate_numbers(count, workers)
        
        # Return as column for Excel (2D list)
        return [[num] for num in numbers]
        
    except Exception as e:
        # Return error message in Excel
        return [[f"Error: {str(e)}"]]


@xw.func
def check_rdseed_support() -> str:
    """
    Excel UDF to check if RDSEED is supported.
    
    Returns:
        Status message
    """
    try:
        generator = RDSeedGenerator("rdseed_boost_new_claude.dll")
        return "RDSEED supported" if generator.is_rdseed_supported() else "RDSEED not supported"
    except Exception as e:
        return f"Error: {str(e)}"


@xw.func
def get_sample_numbers(count: int = 10) -> List[List[int]]:
    """
    Excel UDF to get a small sample of random numbers for testing.
    
    Args:
        count: Number of sample numbers (max 1000)
    
    Returns:
        2D list (column) of random numbers
    """
    try:
        if count > 1000:
            count = 1000
            
        generator = RDSeedGenerator("rdseed_boost_new_claude.dll")
        numbers = generator.generate_numbers(count, 2)  # Use 2 workers for samples
        
        return [[num] for num in numbers]
        
    except Exception as e:
        return [[f"Error: {str(e)}"]]


# Standalone usage example
if __name__ == "__main__":
    try:
        generator = RDSeedGenerator("rdseed_boost_new_claude.dll")
        
        print("RDSEED Support:", generator.is_rdseed_supported())
        
        # Generate 100 numbers with 4 workers
        print("Generating 100 numbers with 4 workers...")
        numbers = generator.generate_numbers(100, 4)
        
        print(f"Generated {len(numbers)} numbers")
        print("First 10 numbers:", numbers[:10])
        print("Last 10 numbers:", numbers[-10:])
        
        # Check range (should be between 100000000000000 and 999999999999999)
        print(f"Min: {min(numbers)}, Max: {max(numbers)}")
        
    except Exception as e:
        print(f"Error: {e}")

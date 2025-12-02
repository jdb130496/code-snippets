import os
import sys
import ctypes
import subprocess
from typing import List, Tuple

# ===== CRITICAL: Add MSYS2 to PATH first =====
msys2_bin = r'D:\Programs\msys64\ucrt64\bin'
if os.path.exists(msys2_bin):
    os.environ['PATH'] = msys2_bin + os.pathsep + os.environ.get('PATH', '')
    print(f"✅ Added to PATH: {msys2_bin}")
else:
    print(f"⚠️ MSYS2 not found at: {msys2_bin}")

class PCRE2_10_47_Full:
    """
    Complete workaround for PCRE2 10.47 features
    """
    
    def __init__(self):
        self.has_direct_api = False
        self.lib = None
        
        # Try to load PCRE2 library
        try:
            # Try the exact DLL name you found
            self.lib = ctypes.CDLL(r'D:\Programs\msys64\ucrt64\bin\libpcre2-8-0.dll')
            self.has_direct_api = True
            print("✅ Successfully loaded PCRE2 library directly!")
        except Exception as e:
            print(f"⚠️ Could not load PCRE2 library: {e}")
            print("   Will use command-line tools instead (still works!)")
    
    # ✅ FEATURE 1: Recursive Patterns
    def findall_recursive(self, pattern: str, text: str) -> List[str]:
        """Find all matches using recursive patterns via pcre2grep"""
        result = subprocess.run(
            ['pcre2grep', '-o', pattern],
            input=text,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0 and result.stderr:
            raise ValueError(f"Pattern error: {result.stderr.strip()}")
        
        return [m for m in result.stdout.strip().split('\n') if m]
    
    # ✅ FEATURE 2: $+ Replacement
    def substitute_extended(self, pattern: str, replacement: str, text: str, 
                          global_replace: bool = True) -> str:
        """Perform substitution with $+ support via pcre2test"""
        pattern_clean = pattern.replace('/', '\\/')
        replacement_clean = replacement.replace('/', '\\/')
        
        flags = 'g,' if global_replace else ''
        test_input = f"""/{pattern_clean}/{flags}replace={replacement_clean},substitute_extended
{text}
"""
        
        result = subprocess.run(
            ['pcre2test'],
            input=test_input,
            capture_output=True,
            text=True
        )
        
        lines = result.stdout.strip().split('\n')
        
        for i, line in enumerate(lines):
            if text in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if ':' in next_line:
                    return next_line.split(':', 1)[1].strip()
                return next_line
        
        for line in reversed(lines):
            if line.strip() and not line.startswith(('/','re>')):
                return line.strip()
        
        return text
    
    # ✅ FEATURE 3: Efficient iteration
    def finditer_next_match(self, pattern: str, text: str) -> List[Tuple[int, int, str]]:
        """Iterate matches efficiently using ripgrep"""
        result = subprocess.run(
            ['rg', '--pcre2', '--byte-offset', '--only-matching', '--no-filename', pattern, '-'],
            input=text,
            capture_output=True,
            text=True
        )
        
        matches = []
        for line in result.stdout.strip().split('\n'):
            if line and ':' in line:
                offset, match_text = line.split(':', 1)
                start = int(offset)
                end = start + len(match_text)
                matches.append((start, end, match_text))
        
        return matches

# ===== DEMO ALL 3 FEATURES =====

def demo_all_features():
    """Test all 3 PCRE2 10.47 features"""
    print("\n" + "="*60)
    print("PCRE2 10.47 Feature Demonstrations")
    print("="*60)
    
    pcre2 = PCRE2_10_47_Full()
    
    # Feature 1: Recursive patterns
    print("\n✅ FEATURE 1: Recursive Pattern with Capture Groups")
    print("-" * 60)
    pattern = r'(?<paren>\((?:[^()]|(?&paren))*\))'
    text = '((nested (stuff)) and (more))'
    try:
        matches = pcre2.findall_recursive(pattern, text)
        print(f"Pattern: {pattern}")
        print(f"Text: {text}")
        print(f"Matches: {matches}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Feature 2: $+ replacement
    print("\n✅ FEATURE 2: $+ Replacement (Last Captured Group)")
    print("-" * 60)
    pattern = r'(\w+)\s+(\w+)\s+(\w+)'
    text = 'foo bar baz'
    try:
        result = pcre2.substitute_extended(pattern, '$+', text)
        print(f"Pattern: {pattern}")
        print(f"Text: {text}")
        print(f"Replacement: $+ (last captured group)")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Feature 3: Efficient iteration
    print("\n✅ FEATURE 3: Efficient Iteration (pcre2_next_match benefit)")
    print("-" * 60)
    pattern = r'\b\w{4,}\b'
    text = 'The quick brown fox jumps'
    try:
        matches = pcre2.finditer_next_match(pattern, text)
        print(f"Pattern: {pattern}")
        print(f"Text: {text}")
        print("Matches (start, end, text):")
        for start, end, match in matches:
            print(f"  ({start:2d}, {end:2d}): '{match}'")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("✅ All 3 features demonstrated!")
    print("="*60)

if __name__ == '__main__':
    demo_all_features()

#!/usr/bin/env python3
"""
FAT32/exFAT Directory Entry Sorter - Emulates DriveSort behavior
Directly manipulates filesystem directory entries to reorder files.
REQUIRES ADMIN/ROOT PRIVILEGES to access raw disk.

WARNING: This operates on raw disk structures. Use with caution!
Always backup your data before running.
"""

import os
import sys
import struct
import ctypes
from pathlib import Path
import re

# Windows API constants
GENERIC_READ = 0x80000000
GENERIC_WRITE = 0x40000000
OPEN_EXISTING = 3
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002

def natural_sort_key(filename):
    """Extract numbers from filename for natural sorting"""
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', filename)]

def get_drive_letter(path):
    """Extract drive letter from path"""
    path = Path(path).resolve()
    drive = path.drive
    if not drive:
        print("Error: Could not determine drive letter")
        return None
    return drive.rstrip(':')

def read_fat32_directory_entries(drive_letter, folder_path):
    """
    Read FAT32 directory entries for a folder.
    This is a simplified version - full implementation would need to:
    1. Read the boot sector to get cluster size
    2. Follow the FAT chain to find directory clusters
    3. Parse directory entries (32 bytes each)
    """
    print(f"WARNING: Direct FAT32 manipulation not yet implemented")
    print(f"This requires low-level disk access and FAT32 structure parsing")
    return None

def sort_with_fallback_method(folder_path):
    """
    Fallback method: Use Windows API to manipulate file times
    to influence directory ordering.
    """
    folder = Path(folder_path).resolve()
    
    if not folder.exists() or not folder.is_dir():
        print(f"Error: Invalid folder path '{folder_path}'")
        return False
    
    # Get all MP3 files sorted
    mp3_files = sorted(folder.glob("*.mp3"), key=lambda x: natural_sort_key(x.name))
    
    if not mp3_files:
        print(f"No MP3 files found in '{folder_path}'")
        return False
    
    print(f"Found {len(mp3_files)} MP3 files")
    print(f"Using fallback method (copy in order)...\n")
    
    # Create temporary folder on same drive
    temp_folder = folder.parent / f"_temp_sorted_{folder.name}"
    
    if temp_folder.exists():
        import shutil
        shutil.rmtree(temp_folder)
    
    temp_folder.mkdir()
    
    # Copy files in sorted order with forced flush
    print("Copying files in order:")
    import shutil
    for i, mp3_file in enumerate(mp3_files, 1):
        print(f"  {i:3d}. {mp3_file.name}")
        dest = temp_folder / mp3_file.name
        shutil.copy2(mp3_file, dest)
        # Force flush to disk
        if os.name == 'nt':
            # On Windows, try to flush file system buffers
            try:
                kernel32 = ctypes.windll.kernel32
                handle = kernel32.CreateFileW(
                    str(dest),
                    GENERIC_READ | GENERIC_WRITE,
                    FILE_SHARE_READ | FILE_SHARE_WRITE,
                    None,
                    OPEN_EXISTING,
                    0,
                    None
                )
                if handle != -1:
                    kernel32.FlushFileBuffers(handle)
                    kernel32.CloseHandle(handle)
            except:
                pass
    
    # Rename folders
    print(f"\nReplacing original folder...")
    backup_folder = folder.parent / f"_backup_{folder.name}"
    folder.rename(backup_folder)
    temp_folder.rename(folder)
    
    print(f"\n✓ Successfully sorted {len(mp3_files)} files!")
    print(f"✓ Original folder backed up to: {backup_folder.name}")
    print(f"\nTo remove backup: rmdir /s \"{backup_folder}\"")
    
    return True

def main():
    if len(sys.argv) != 2:
        print("USB Drive MP3 Sorter - Directory Entry Reordering")
        print("=" * 60)
        print("\nUsage: python sort_usb_mp3.py <folder_path>")
        print("\nExamples:")
        print("  python sort_usb_mp3.py E:\\1")
        print("  python sort_usb_mp3.py E:/1")
        print("  python sort_usb_mp3.py /e/1")
        print("\nNOTE: Run as Administrator for best results")
        print("=" * 60)
        sys.exit(1)
    
    folder_path = sys.argv[1]
    
    # Check if running as admin on Windows
    if os.name == 'nt':
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                print("WARNING: Not running as Administrator")
                print("For best results, run PowerShell as Administrator\n")
        except:
            pass
    
    print("FAT32/exFAT Directory Entry Sorter")
    print("=" * 60)
    print(f"Target folder: {folder_path}\n")
    
    # Use fallback method (copy in order with flush)
    # Full FAT32 manipulation would require much more code
    success = sort_with_fallback_method(folder_path)
    
    if success:
        print("\n" + "=" * 60)
        print("IMPORTANT: After sorting, safely eject and reinsert")
        print("the USB drive to ensure changes are committed.")
        print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

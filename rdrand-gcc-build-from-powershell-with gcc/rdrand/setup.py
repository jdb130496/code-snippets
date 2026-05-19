from setuptools import setup, Extension
import sysconfig
import sys
import os

# Get the correct include directory for the active Python
python_include = sysconfig.get_path('include')

# Get library information
lib_dir = sysconfig.get_config_var('LIBDIR')
if not lib_dir:
    # Fallback for Windows Python
    lib_dir = os.path.join(sys.prefix, 'libs')

py_version_nodot = f"{sys.version_info.major}{sys.version_info.minor}"

# Setup library linking
extra_link_args = []
libraries = []
library_dirs = [lib_dir] if lib_dir else []

if sys.platform == 'win32':
    # For Windows Python with MinGW/GCC
    # Windows Python has pythonXY.lib in the libs directory
    libraries = [f'python{py_version_nodot}']
    print(f"Building for Windows Python with library: python{py_version_nodot}")
    print(f"Library directory: {lib_dir}")
    print(f"Include directory: {python_include}")

# Create extension with correct paths
rdrand_ext = Extension(
    '_rdrand',
    sources=['rdrand.c'],
    include_dirs=[python_include],
    library_dirs=library_dirs,
    libraries=libraries,
    extra_link_args=extra_link_args,
)

setup(
    ext_modules=[rdrand_ext],
)

from setuptools import setup, Extension
import sysconfig
import os

CLANG = 'D:/Programs/clang/bin'

# Patch ALL vars that customize_compiler reads - all None on MSVC-built Python
config_vars = sysconfig.get_config_vars()
config_vars['CC']          = f'{CLANG}/clang.exe'
config_vars['CXX']         = f'{CLANG}/clang++.exe'
config_vars['AR']          = f'{CLANG}/llvm-ar.exe'
config_vars['ARFLAGS']     = 'rcs'
config_vars['RANLIB']      = f'{CLANG}/llvm-ranlib.exe'
config_vars['LDSHARED']    = f'{CLANG}/clang.exe -shared'
config_vars['LDCXXSHARED'] = f'{CLANG}/clang++.exe -shared'
config_vars['CFLAGS']      = '-O2'
config_vars['CCSHARED']    = ''
config_vars['SHLIB_SUFFIX']= '.pyd'

# Also mirror to environment - customize_compiler checks os.environ too
os.environ['CC']           = f'{CLANG}/clang.exe'
os.environ['CXX']          = f'{CLANG}/clang++.exe'
os.environ['AR']           = f'{CLANG}/llvm-ar.exe'
os.environ['ARFLAGS']      = 'rcs'
os.environ['RANLIB']       = f'{CLANG}/llvm-ranlib.exe'
os.environ['LDSHARED']     = f'{CLANG}/clang.exe -shared'
os.environ['LDCXXSHARED']  = f'{CLANG}/clang++.exe -shared'
os.environ['CFLAGS']       = '-O2'
os.environ['CCSHARED']     = ''

python_include = sysconfig.get_path('include')

rdrand_ext = Extension(
    '_rdrand',
    sources=['rdrand.c'],
    include_dirs=[python_include],
    extra_compile_args=['-mrdrnd', '-mrdseed'],
)

setup(ext_modules=[rdrand_ext])

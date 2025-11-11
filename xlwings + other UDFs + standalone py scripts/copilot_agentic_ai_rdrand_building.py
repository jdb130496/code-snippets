import os
import zipfile

# Create the directory structure for the package
os.makedirs("rand", exist_ok=True)

# Create randmodule.c with inline assembly for Linux
with open("rand/randmodule.c", "w") as f:
    f.write(r'''
#include <Python.h>
#include <stdint.h>

static PyObject* rdrand64(PyObject* self, PyObject* args) {
    uint64_t val;
    unsigned char ok;

    __asm__ __volatile__(
        "rdrand %0; setc %1"
        : "=r" (val), "=qm" (ok)
    );

    if (!ok)
        Py_RETURN_NONE;

    return PyLong_FromUnsignedLongLong(val);
}

static PyObject* rdseed64(PyObject* self, PyObject* args) {
    uint64_t val;
    unsigned char ok;

    __asm__ __volatile__(
        "rdseed %0; setc %1"
        : "=r" (val), "=qm" (ok)
    );

    if (!ok)
        Py_RETURN_NONE;

    return PyLong_FromUnsignedLongLong(val);
}

static PyMethodDef RandMethods[] = {
    {"rdrand64", rdrand64, METH_NOARGS, "Return 64-bit random number using RDRAND"},
    {"rdseed64", rdseed64, METH_NOARGS, "Return 64-bit seed using RDSEED"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef randmodule = {
    PyModuleDef_HEAD_INIT,
    "rand",
    NULL,
    -1,
    RandMethods
};

PyMODINIT_FUNC PyInit_rand(void) {
    return PyModule_Create(&randmodule);
}
''')

# Create rdrand.asm for Windows
with open("rand/rdrand.asm", "w") as f:
    f.write(r'''
.code

rdrand64 PROC
    mov ecx, 10
retry:
    rdrand rax
    jc success
    loop retry
    xor rax, rax
success:
    ret
rdrand64 ENDP

rdseed64 PROC
    mov ecx, 10
retry_seed:
    rdseed rax
    jc success_seed
    loop retry_seed
    xor rax, rax
success_seed:
    ret
rdseed64 ENDP

END
''')

# Create setup.py with platform-specific logic
with open("setup.py", "w") as f:
    f.write(r'''
import sys
import os
from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext

class CustomBuildExt(build_ext):
    def build_extensions(self):
        if sys.platform == "win32":
            self.compiler.compile(["rand/rdrand.asm"], output_dir="rand")
            for ext in self.extensions:
                ext.extra_objects = ["rand/rdrand.obj"]
        build_ext.build_extensions(self)

ext_modules = [
    Extension(
        "rand",
        sources=["rand/randmodule.c"],
        extra_compile_args=["-march=native"] if sys.platform != "win32" else [],
    )
]

setup(
    name="rand",
    version="1.0",
    description="Cross-platform RDRAND/RDSEED Python extension",
    ext_modules=ext_modules,
    cmdclass={"build_ext": CustomBuildExt},
)
''')

# Create setup.cfg
with open("setup.cfg", "w") as f:
    f.write(r'''
[metadata]
name = rand
version = 1.0
description = Cross-platform RDRAND/RDSEED Python extension

[options]
zip_safe = False
''')

# Create pyproject.toml
with open("pyproject.toml", "w") as f:
    f.write(r'''
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"
''')

# Create README.md with full build instructions
with open("README.md", "w") as f:
    f.write(r'''
# rand: Cross-platform RDRAND/RDSEED Python Extension

## Build Instructions

### Linux / MSYS2 (GCC)

1. Ensure you have Python 3.14+ and GCC installed.
2. Run the following command to install the package:

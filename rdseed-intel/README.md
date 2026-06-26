Documentation in brief:

This build (python custom library) is tested only on Windows with msvc in the path. I built it from powershell. But it can also be built (may be with some changes on msys or linux). Do not know about MacOS.

Building requires first scikit-build-core

Install it with pip install scikit-build-core

Advantage of this package (hwrng) is, it generates random bytes using intel's hardware entropy with rdseed as backbone. You can see that in the source c file. A simple example to generate multiple random integers using this hwrng library isalso packed here. 

Command to build:

pip install -e . --no-build-isolation

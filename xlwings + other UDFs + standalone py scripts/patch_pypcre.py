content = open(r'D:\dev\PyPcre\setup_utils.py', encoding='utf-8').read()

old1 = (
    '            # On Windows, force MSVC and the /MD runtime. Never let CMake pick MinGW.\n'
    '            if _is_windows_platform():\n'
    '                vs_gen = os.environ.get("CMAKE_GENERATOR", _detect_vs_generator())\n'
    '                cmake_args += [\n'
    '                    "-G", vs_gen,\n'
    '                    "-A", "x64",\n'
    '                    "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL",\n'
    '                ]'
)
new1 = (
    '            # On Windows, use Ninja+clang-cl if CMAKE_GENERATOR=Ninja, else MSVC.\n'
    '            if _is_windows_platform():\n'
    '                vs_gen = os.environ.get("CMAKE_GENERATOR")\n'
    '                if vs_gen and vs_gen.lower() == "ninja":\n'
    '                    cmake_args += ["-G", "Ninja", "-DCMAKE_BUILD_TYPE=Release"]\n'
    '                    if os.environ.get("CMAKE_C_COMPILER"):\n'
    '                        cmake_args += ["-DCMAKE_C_COMPILER=" + os.environ["CMAKE_C_COMPILER"]]\n'
    '                    if os.environ.get("CMAKE_CXX_COMPILER"):\n'
    '                        cmake_args += ["-DCMAKE_CXX_COMPILER=" + os.environ["CMAKE_CXX_COMPILER"]]\n'
    '                    if os.environ.get("CMAKE_LINKER"):\n'
    '                        cmake_args += ["-DCMAKE_LINKER=" + os.environ["CMAKE_LINKER"]]\n'
    '                else:\n'
    '                    vs_gen = vs_gen or _detect_vs_generator()\n'
    '                    cmake_args += [\n'
    '                        "-G", vs_gen,\n'
    '                        "-A", "x64",\n'
    '                        "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL",\n'
    '                    ]'
)

old2 = (
    'def _get_test_compiler() -> CCompiler | None:\n'
    '    global _COMPILER_INITIALIZED, _COMPILER_INSTANCE\n'
    '    if _COMPILER_INITIALIZED:\n'
    '        return _COMPILER_INSTANCE\n'
    '    _COMPILER_INITIALIZED = True\n'
    '    try:\n'
    '        compiler = new_compiler()\n'
    '        customize_compiler(compiler)\n'
    '    except Exception:\n'
    '        _COMPILER_INSTANCE = None\n'
    '    else:\n'
    '        _COMPILER_INSTANCE = compiler\n'
    '    return _COMPILER_INSTANCE'
)
new2 = (
    'def _get_test_compiler() -> CCompiler | None:\n'
    '    global _COMPILER_INITIALIZED, _COMPILER_INSTANCE\n'
    '    if _COMPILER_INITIALIZED:\n'
    '        return _COMPILER_INSTANCE\n'
    '    _COMPILER_INITIALIZED = True\n'
    '    try:\n'
    '        if os.environ.get("CMAKE_C_COMPILER", "").endswith("clang-cl.exe"):\n'
    '            _COMPILER_INSTANCE = None\n'
    '            return _COMPILER_INSTANCE\n'
    '        compiler = new_compiler()\n'
    '        customize_compiler(compiler)\n'
    '    except Exception:\n'
    '        _COMPILER_INSTANCE = None\n'
    '    else:\n'
    '        _COMPILER_INSTANCE = compiler\n'
    '    return _COMPILER_INSTANCE'
)

if old1 in content:
    content = content.replace(old1, new1)
    print('Patch 1 applied')
else:
    print('Patch 1 FAILED')

if old2 in content:
    content = content.replace(old2, new2)
    print('Patch 2 applied')
else:
    print('Patch 2 FAILED')

open(r'D:\dev\PyPcre\setup_utils.py', 'w', encoding='utf-8').write(content)

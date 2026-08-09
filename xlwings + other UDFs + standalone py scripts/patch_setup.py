content = open(r'D:\dev\PyPcre\setup.py', encoding='utf-8').read()

old = (
    '            if compiler_supports_flags(["/std:c11"], code=c11_probe):\n'
    '                extra_compile_args.append("/std:c11")\n'
    '            elif compiler_supports_flags(["/std:clatest"], code=c11_probe):\n'
    '                extra_compile_args.append("/std:clatest")\n'
    '            else:\n'
    '                raise RuntimeError("MSVC requires /std:c11 or newer for atomics support")'
)
new = (
    '            if compiler_supports_flags(["/std:c11"], code=c11_probe):\n'
    '                extra_compile_args.append("/std:c11")\n'
    '            elif compiler_supports_flags(["/std:clatest"], code=c11_probe):\n'
    '                extra_compile_args.append("/std:clatest")\n'
    '            elif compiler_supports_flags(["-std=c11"], code=c11_probe):\n'
    '                extra_compile_args.append("-std=c11")\n'
    '            else:\n'
    '                raise RuntimeError("MSVC requires /std:c11 or newer for atomics support")'
)

if old in content:
    content = content.replace(old, new)
    print('Patch applied')
else:
    print('Patch FAILED - old string not found')

open(r'D:\dev\PyPcre\setup.py', 'w', encoding='utf-8').write(content)

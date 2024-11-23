import pythonmonkey as pm

def get_pythonmonkey_version():
    # Get the version of pythonmonkey
    version = pm.eval("process.version")
    return version

if __name__ == "__main__":
    version = get_pythonmonkey_version()
    print(version)


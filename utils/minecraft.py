import os

if os.name == "posix":
    print("WARNING: minecraft is not supported on Linux/Mac")
else:
    from .windows.minecraft import *

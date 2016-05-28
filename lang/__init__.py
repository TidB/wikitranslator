# Automatically adding all files in the current dir to __all__ so I can import
# everything dynamically without having to worry about adding items to the list.
from os.path import dirname, basename, isfile
import glob
modules = glob.glob(dirname(__file__)+"/*.py")
__all__ = [
    basename(f)[:-3]
    for f in modules if isfile(f)
    if not basename(f).startswith('_')
    ]

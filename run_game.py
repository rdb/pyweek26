#! /usr/bin/env python

import sys

try:
    import panda3d
    import numpy
except ImportError as ex:
    print("""
===================================================

This game requires Panda3D 1.10 and numpy >1.8.0

Please run the following command to install them:

    pip install -r requirements.txt

===================================================
""")
    print(repr(ex))
    sys.exit(1)

from gamelib import main
main()

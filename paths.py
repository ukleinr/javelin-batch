# -*- coding: utf-8 -*-
"""Object-relative data paths, anchored on this module's location.

Resolves the object's data directories from this file's location rather than
the process CWD, so pipeline scripts work regardless of where they are invoked
while still resolving to the same tree in normal use (run from ``scripts/``).
Must stay Python 2.7 compatible.
"""
import os

_SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
OBJECT_DIR = os.path.dirname(_SCRIPTS_DIR)

JAV_DATA = os.path.join(OBJECT_DIR, 'jav_data')
LIGHT_CURVES = os.path.join(OBJECT_DIR, 'light_curves')
RESULTS = os.path.join(OBJECT_DIR, 'results')

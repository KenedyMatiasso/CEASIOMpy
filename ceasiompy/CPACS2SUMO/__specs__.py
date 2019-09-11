#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut

# ===== RCE integration =====

RCE = {
    "name": "CPACS2SUMO",
    "description": "Convert CPACS .xml file into SUMO .smx file",
    "exec": "pwd\npython cpacs2sumo.py",
    "author": "Aidan Jungo",
    "email": "aidan.jungo@cfse.ch",
}

# ===== CPACS inputs and outputs =====

cpacs_inout = CPACSInOut()

# ----- Input -----

# No inputs value for this modules

# ----- Output -----

# No outputs value for this modules

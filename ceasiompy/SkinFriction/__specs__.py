#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from ceasiompy.utils.moduleinterfaces import CPACSInOut, CEASIOM_XPATH

cpacs_inout = CPACSInOut()

# ===== Input =====

cpacs_inout.add_input(
        var_name='wetted_area',
        default_value=None,
        unit='m^2',
        descr='Wetted area of the aircraft (calculated by SU2)',
        cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wettedArea',
        )

cpacs_inout.add_input(
        var_name='cruise_speed',
        default_value=272,
        unit='m/s',
        descr='Aircraft cruise speed',
        cpacs_path=CEASIOM_XPATH + '/ranges/cruiseSpeed',
        )

cpacs_inout.add_input(
        var_name='cruise_alt',
        default_value=12000,
        unit='m',
        descr='Aircraft cruise altitude',
        cpacs_path=CEASIOM_XPATH + '/ranges/cruiseAltitude',
        )

# ===== Output =====

cpacs_inout.add_output(
        var_name='cd0',
        default_value=None,
        unit='1',
        descr='Skin friction drag coefficient',
        cpacs_path=CEASIOM_XPATH + '/aerodynamics/su2/cd0',
        )

cpacs_inout.add_output(
        var_name='wing_area',
        default_value=None,
        unit='m^2',
        descr='Wing area of the main (largest) wing',
        cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wingArea',
        )

cpacs_inout.add_output(
        var_name='wing_span',
        default_value=None,
        unit='m',
        descr='Wing span of the main (largest) wing',
        cpacs_path=CEASIOM_XPATH + '/geometry/analysis/wingSpan',
        )
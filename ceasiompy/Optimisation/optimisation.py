"""
CEASIOMpy: Conceptual Aircraft Design Software

Developed by CFS ENGINEERING, 1015 Lausanne, Switzerland

Python version: >=3.6

| Author: Aidan jungo
| Creation: 2020-24-02
| Last modifiction: 2020-06-04

TODO:

    * Class instead of dictionnary ?
    * Add/modify the optimisation parameters
"""

# =============================================================================
#   IMPORTS
# =============================================================================

import datetime
import openmdao.api as om
import numpy as np

from re import split as splt
from ceasiompy.Optimisation.func.dictionnary import init_dict, update_res_var_dict
import ceasiompy.utils.workflowfunctions as wkf
import ceasiompy.utils.ceasiompyfunctions as ceaf
import ceasiompy.utils.cpacsfunctions as cpsf
import ceasiompy.utils.apmfunctions as apmf
import ceasiompy.utils.moduleinterfaces as mi
import ceasiompy.utils.optimfunctions as opf

from ceasiompy.CPACSUpdater.cpacsupdater import update_cpacs_file

from ceasiompy.utils.ceasiomlogger import get_logger
log = get_logger(__file__.split('.')[0])

SU2_XPATH = '/cpacs/toolspecific/CEASIOMpy/aerodynamics/su2'

# =============================================================================
#   GLOBAL VARIABLES
# =============================================================================

Rt = opf.Routine
counter = 0

# =============================================================================
#   CLASSES
# =============================================================================


class objective_function(om.ExplicitComponent):
    """Class to define function and variables for openmdao."""

    def setup(self):
        """Create function inputs and outputs."""
        # Add inputs
        for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
            self.add_input(key, val=listval[0])

        # Add outputs
        self.add_output(Rt.objective)

        # Finite difference all partials.
        self.declare_partials('*', '*', method='exact')

    def compute(self, inputs, outputs):
        """Launch subroutine to compute objective function."""
        # Add new variable value to the list in the dictionnay
        for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
            listval.append(inputs[key][0])

        # Evaluate the function to optimize
        outputs[Rt.objective] = one_iteration()


class constraint(om.ExplicitComponent):
    """Class to define the constraints or target that are not explicit design variables."""

    def setup(self):
        """Create function inputs and outputs."""
        # Add output
        for key, (name, listval, lower_bound, upper_bound, getcommand) in res_var_dict.items():
            self.add_output(name, val=listval[0])

    def compute(self, inputs, outputs):
        """Retrieve values of constrains."""
        for key, (name, listval, lower_bound, upper_bound, getcmd) in res_var_dict.items():
            outputs[name] = listval[-1]

        # outputs['passengers'] = get_val()

# =============================================================================
#   FUNCTIONS
# =============================================================================


def run_routine():
    """
    Run optimisation with openmdao.

    Function 'run_routine' is used to define the optimisation problem for
    openmdao. The different parameter to define variables are passed through a
    global dictionnay (for now).

    Source:
        *http://openmdao.org/twodocs/versions/latest/getting_started/index.html

    """
    # sInitialize dictionnaries
    # init_dict()

    # Build the model
    prob = om.Problem()
    model = prob.model

    # Build model components
    indeps = model.add_subsystem('indeps', om.IndepVarComp())
    model.add_subsystem('objective', objective_function())
    model.add_subsystem('const', constraint())

    # Choose between optimizer or driver
    if Rt.type == 'DoE':
        driver = prob.driver = om.DOEDriver(om.UniformGenerator(num_samples=10))
        # 2->9 3->81
        # driver = prob.driver = om.DOEDriver(om.FullFactorialGenerator(3))
    elif Rt.type == 'Optim':
        driver = prob.driver = om.ScipyOptimizeDriver()
        # SLSQP,COBYLA,shgo,TNC
        driver.options['optimizer'] = Rt.driver
        driver.options['maxiter'] = 10
        # driver.options['tol'] = 1e-2

    # Connect problem components to model components

    # Design variable
    for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
        norm = int(np.log10(abs(listval[0])+1)+1)
        indeps.add_output(key, listval[0], ref=norm, ref0=0)
        model.connect('indeps.'+key, 'objective.'+key)
        model.add_design_var('indeps.'+key, lower=minval, upper=maxval)

    # Constrains
    for key, (name, listval, minval, maxval, getcommand) in res_var_dict.items():
        if name == "cms":
            model.add_constraint('const.'+name, -0.1, 0.1)

    # Objective function
    model.add_objective('objective.{}'.format(Rt.objective))

    # Recorder
    # TODO : make more robust path finding
    path = '../Optimisation/'
    driver.add_recorder(om.SqliteRecorder(path + 'Driver_recorder.sql'))

    # Run
    prob.setup()
    prob.run_driver()
    prob.cleanup()

    # Results
    log.info('=========================================')
    log.info('min = ' + str(prob['objective.{}'.format(Rt.objective)]))

    for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
        log.info(name + ' = ' + str(prob['indeps.'+key]))

    log.info('Variable history')
    for key, (name, listval, minval, maxval, setcommand, getcommand) in design_var_dict.items():
        log.info(name + ' => ' + str(listval))

    log.info('=========================================')

    # Generate plots, maybe make a dynamic plot
    opf.read_results()


def one_iteration():
    """
    Compute the objective function.

    Function 'one_iteration' will exectute in order all the module contained
    in '...' and extract the ... value from the last CPACS file, this value will
    be returned to the optimizer CPACSUpdater....

    """
    global counter
    counter += 1

    # Create the parameter in CPACS with 'CPACSUpdater' module
    cpacs_path = mi.get_toolinput_file_path('CPACSUpdater')
    cpacs_out_path = mi.get_tooloutput_file_path('CPACSUpdater')

    tixi = cpsf.open_tixi(cpacs_path)
    wkdir_path = ceaf.create_new_wkdir(Rt.date)
    WKDIR_XPATH = '/cpacs/toolspecific/CEASIOMpy/filesPath/wkdirPath'
    tixi.updateTextElement(WKDIR_XPATH, wkdir_path)

    # TODO: improve this part! (maybe move somewhere else)
    # To delete coef from previous iter
    aeromap_uid = cpsf.get_value(tixi, SU2_XPATH + '/aeroMapUID')
    Coef = apmf.get_aeromap(tixi, aeromap_uid)
    apmf.delete_aeromap(tixi, aeromap_uid)
    apmf.create_empty_aeromap(tixi, aeromap_uid, 'test_optim')
    apmf.save_parameters(tixi, aeromap_uid, Coef)
    cpsf.close_tixi(tixi, cpacs_path)

    # Update the CPACS file with the parameters contained in design_var_dict
    update_cpacs_file(cpacs_path, cpacs_out_path, design_var_dict)

    # Save the CPACS file
    if counter % 1 == 0:
        wkf.copy_module_to_module('CPACSUpdater', 'out', 'Optimisation',
                                  'iter_{}'.format(counter))

    # Run optimisation sub workflow
    wkf.copy_module_to_module('CPACSUpdater', 'out', Rt.modules[0], 'in')
    wkf.run_subworkflow(Rt.modules)
    wkf.copy_module_to_module(Rt.modules[-1], 'out', 'CPACSUpdater', 'in')

    # Extract results  TODO: improve this part
    cpacs_results_path = mi.get_tooloutput_file_path(Rt.modules[-1])
    log.info('Results will be extracted from:' + cpacs_results_path)
    tixi = cpsf.open_tixi(cpacs_results_path)

    # Update the constrains values
    update_res_var_dict(tixi)
    return compute_obj()


def compute_obj():
    """
    Interpret the objective variable command.

    Get all the values needed to compute the objective function and
    evaluates its expression.

    Returns
    -------
    None.

    """
    # Get variable keys from objective function string
    var_list = splt('[+*/-]', Rt.objective)

    # Create local variable and assign value
    for v in var_list:
        exec('{} = res_var_dict["{}"][1][-1]'.format(v, v))

    result = eval(Rt.objective)
    log.info('Objective function {} : {}'.format(Rt.objective, result))
    # Evaluate objective function expression
    return -result


def routine_setup(modules, routine_type):
    """
    Set up optimisation.

    Retrieve the list of modules to use in the optimization
    loop and launches the optimization process.

    """
    log.info('----- Start of Optimisation module -----')

    global Rt, design_var_dict, res_var_dict

    # Setup parameters of the routine (TODO : implement in the GUI)
    Rt.type = routine_type
    Rt.modules = modules
    Rt.driver = 'COBYLA'
    Rt.objective = 'cl/cd'
    Rt.date = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')

    cpacs_path = mi.get_toolinput_file_path(modules[0])

    res_var_dict, design_var_dict = init_dict(cpacs_path)

    # Copy initial model before the optimisation process
    wkf.copy_module_to_module(modules[0], 'out', 'Optimisation', 'initial')

    # Copy to CPACSUpdater to pass to next modules
    wkf.copy_module_to_module(modules[0], 'out', 'CPACSUpdater', 'in')

    # Display routine info
    log.info('------ Problem description ------')
    log.info('Routine type : {}'.format(routine_type))
    log.info('Objective function : {}'.format(Rt.objective))
    [log.info('Design variables : {}'.format(k)) for k in design_var_dict.keys()]
    [log.info('Constrains : {}'.format(k)) for k in res_var_dict.keys()]

    run_routine()

    log.info('----- End of Optimisation module -----')


if __name__ == '__main__':
    # Specify parameters already implemented in the SettingsGUI
    module_list = ['WeightConventional']
    rt_type = 'Optim'

    routine_setup(module_list, rt_type)
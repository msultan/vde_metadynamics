#!/bin/env python
from jinja2 import Template
import numpy as np



plumed_plain_metad_template = Template("METAD ARG={{arg}} SIGMA={{sigma}} HEIGHT={{height}} "+\
                                       "FILE={{hills}} TEMP={{temp}} PACE={{pace}} LABEL={{label}}")

base_metad_script="METAD ARG={{arg}} SIGMA={{sigma}} HEIGHT={{height}} "+\
                    "FILE={{hills}} TEMP={{temp}} PACE={{pace}} LABEL={{label}}"

bias_factor_format = "BIASFACTOR={{biasfactor}}"

interval_format = "INTERVAL={{interval}}"

grid_format = "GRID_MIN={{GRID_MIN}} GRID_MAX={{GRID_MAX}}"

plumed_wall_template = Template("{{wall_type}}_WALLS ARG={{arg}} AT={{at}} "
                         "KAPPA={{kappa}} EXP={{exp}} EPS={{eps}} OFFSET={{offset}} LABEL={{label}}")

plumed_print_template = Template("PRINT ARG={{arg}} STRIDE={{stride}} FILE={{file}} ")



def render_metad_code(arg="tic_0", sigma=0.2, height=1.0, hills="HILLS",biasfactor=40,
                      temp=300,interval=None, grid=None,
                      label="metad",pace=1000, walker_n = None, walker_id=None,
                      **kwargs):

    output=[]
    base_metad_script="METAD ARG={{arg}} SIGMA={{sigma}} HEIGHT={{height}} "+\
                    "FILE={{hills}} TEMP={{temp}} PACE={{pace}} LABEL={{label}}"
    bias_factor_format = "BIASFACTOR={{biasfactor}}"
    interval_format = "INTERVAL={{interval}}"
    grid_format = "GRID_MIN={{grid_min}} GRID_MAX={{grid_max}}"
    walker_format="WALKERS_N={{walker_n}} WALKERS_ID={{walker_id}} "+\
                   "WALKERS_DIR={{walker_dir}} WALKERS_RSTRIDE={{walker_stride}}"
    if biasfactor is not None:
        base_metad_script = ' '.join((base_metad_script, bias_factor_format))
    if interval is not None:
        base_metad_script = ' '.join((base_metad_script, interval_format))
    if grid is not None:
        base_metad_script = ' '.join((base_metad_script, grid_format))
    if walker_id is not None:
        base_metad_script = ' '.join((base_metad_script,walker_format))
        walker_stride = pace * 10
        if ',' in arg:
          walker_dir = "../../data_tic0"
        elif arg.startswith("l"):
          walker_dir = "../../data_tic0"
        else:
          walker_dir = "../../data_%s"%arg
    else:
        walker_stride=walker_dir=None
    plumed_metad_template = Template(base_metad_script)

    plumed_script = plumed_metad_template

    if grid is None:
        grid_min=grid_max=0
    else:
        grid_min = grid[0]
        grid_max = grid[1]
    if interval is None:
        interval=[0]

    output.append(plumed_script.render(arg=arg,
                         sigma=sigma,
                         height=height,
                         hills=hills,
                         biasfactor=biasfactor,
                         interval=','.join(map(str,interval)),
                         grid_min=grid_min,
                         grid_max=grid_max,
                         label=label,
                         pace=pace,
                         temp=temp,
                         walker_id=walker_id,
                         walker_n=walker_n,
                         walker_stride=walker_stride,
                         walker_dir=walker_dir) +"\n")
    return ''.join(output)


def render_metad_bias_print(arg="tic_0,metad.bias",stride=1000,file="BIAS"):
    """
    :param arg: tic name
    :param stride: stride for printing
    :param label: label for printing
    :param file:
    :return:
    """
    output=[]
    output.append(plumed_print_template.render(arg=arg,
                                               stride=stride,
                                               file=file))

    return ''.join(output)
#!/bin/env python
from jinja2 import Template
import numpy as np

plumed_matheval_template = Template("MATHEVAL ARG={{arg}} FUNC={{func}} LABEL={{label}} PERIODIC={{periodic}} ")

plumed_combine_template = Template("COMBINE LABEL={{label}} ARG={{arg}} COEFFICIENTS={{coefficients}} "+\
                                    "PERIODIC={{periodic}} ")
plumed_wall_template = Template("{{wall_type}}_WALLS ARG={{arg}} AT={{at}} "
                         "KAPPA={{kappa}} EXP={{exp}} EPS={{eps}} OFFSET={{offset}} LABEL={{label}}")



def render_tic(tica_mdl, tic_index=0,input_label_prefix="f",output_label_prefix="tic"):
    output = []
    inds = np.nonzero(tica_mdl.components_[tic_index,:])[0]

    feature_labels = ["%s0_%d"%(input_label_prefix,i) for i in inds]

    tic_coefficient = tica_mdl.components_[tic_index,inds]
    if tica_mdl.kinetic_mapping:
        raise ValueError("Sorry but kinetic mapping or is not supported for now")

    arg=','.join(feature_labels)
    tic_coefficient = ','.join(map(str,tic_coefficient))
    label = "%s_%d"%(output_label_prefix,tic_index)

    output.append(plumed_combine_template.render(arg=arg,
                                   coefficients=tic_coefficient,
                                   label=label,
                                   periodic="NO") +"\n")
    return ''.join(output)

def render_tic_wall(arg,wall_limts,**kwargs):
    """
    :param arg: tic name
    :param stride: stride for printing
    :param label: label for printing
    :param file:
    :return:
    """
    output=[]
    for i,wall_type in enumerate(["LOWER","UPPER"]):
        output.append(plumed_wall_template.render(wall_type=wall_type,
                                                  arg=arg,
                                                  at=wall_limts[i],
                                                  kappa=150,
                                                  exp=2,
                                                  eps=1,
                                                  offset=0,
                                                  label=wall_type.lower()))
        output.append("\n")
    return ''.join(output)
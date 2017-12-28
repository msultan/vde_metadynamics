#!/bin/env python

from jinja2 import Template
from msmbuilder.utils import load
import numpy as np
import torch


plumed_torsion_template = Template("TORSION ATOMS={{atoms}} LABEL={{label}} ")

plumed_matheval_template = Template("MATHEVAL ARG={{arg}} FUNC={{func}} LABEL={{label}} PERIODIC={{periodic}} ")

plumed_combine_template = Template("COMBINE LABEL={{label}} ARG={{arg}} COEFFICIENTS={{coefficients}} "+\
                                    "PERIODIC={{periodic}} ")
plumed_print_template = Template("PRINT ARG={{arg}} STRIDE={{stride}} FILE={{file}} ")




def create_neural_bias(nb, bias, label):
    arg = ",".join([nb])
    f = "+".join(["x", bias])
    return plumed_matheval_template.render(arg=arg, func=f,\
                                           label=label,periodic="NO")
def create_sigmoid(arg, label):
    f = "1/(1+exp(-x))"
    return plumed_matheval_template.render(arg=arg, func=f,\
                                           label=label,periodic="NO")

def create_swish(arg, label):
    f = "x/(1+exp(-x))"
    return plumed_matheval_template.render(arg=arg, func=f,\
                                           label=label,periodic="NO")

def render_print_val(arg,stride=1,file="CV"):
    return plumed_print_template.render(arg=arg,
                                       stride=stride,
                                       file=file)


def render_fc_layer(layer_indx, lp):
    output=[]
    for i in np.arange(lp.out_features):
        if layer_indx==0:
            arg=','.join(["f%d_%d"%(layer_indx-1,j) for j in range(lp.in_features)])
        else:
            arg=','.join(["l%d_%d"%(layer_indx-1,j) for j in range(lp.in_features)])

        weights = ','.join(map(str,lp.weight[i].data.tolist()))
        bias =','.join(map(str,lp.bias[i].data.tolist()))

        # combine without bias
        non_bias_label = "l%d_%dnb"%(layer_indx, i)
        output.append(plumed_combine_template.render(arg = arg,
                                   coefficients = weights,
                                   label=non_bias_label,
                                   periodic="NO") +"\n")
        # now add the bias
        bias_label = "l%d_%d"%(layer_indx, i)
        output.append(create_neural_bias(non_bias_label, bias, bias_label))
        output.append("\n")
    return ''.join(output)

# def render_network(net):
#     output =[]
#     # Start by evaluating the actual dihedrals + sin-cosine transform aka the input features
#     output.append(write_df(net.df))
#     index = 0
#     # Go over every layer of the netowrk
#     for lp in net.children():
#         index += 1
#         if str(lp).startswith("Linear"):
#             output.append(render_fc_layer(index, lp))
#         elif str(lp).startswith("Sigmoid"):
#             output.append(render_sigmoid_layer(index, lp,hidden_size=net.hidden_size))
#         else:
#             raise ValueError("Only Linear and Sigmoid Layers are supported for now")
#     # Lastly, we want to print out the values from the last layer. This becomes our CV.
#     arg = "l%d0"%index
#     output.append(render_print_val(arg))
#     return ''.join(output)



# this cretes a sigmoid layer
def render_sigmoid_layer(layer_indx, lp, hidden_size=50):
    output=[]
    for i in np.arange(hidden_size):
        arg="l%d_%d"%(layer_indx-1, i)
        label = "l%d_%d"%(layer_indx, i)
        output.append(create_sigmoid(arg, label))
        output.append("\n")

    return ''.join(output)

# this cretes a sigmoid layer
def render_swish_layer(layer_indx, lp, hidden_size=50):
    output=[]
    for i in np.arange(hidden_size):
        arg="l%d_%d"%(layer_indx-1, i)
        label = "l%d_%d"%(layer_indx, i)
        output.append(create_swish(arg, label))
        output.append("\n")

    return ''.join(output)

def render_network(model):
    model.dtype = torch.DoubleTensor
    model.use_cuda =False
    model.cpu()
    model.double()
    output =[]
    index = 0
    for ind,i in enumerate([model.encoder.input_layer, model.encoder.hidden_network,model.encoder.output_layer]):

        if ind in [0,2]:
            for lp in i:
                index += 1
                if str(lp).startswith("Linear"):
                    output.append(render_fc_layer(index, lp))
                elif str(lp).startswith("Sigmoid"):
                    output.append(render_sigmoid_layer(index, lp,hidden_size=model.encoder.hidden_size))
                elif str(lp).startswith("Swish"):
                    output.append(render_swish_layer(index, lp,hidden_size=model.encoder.hidden_size))
                elif str(lp).startswith("Dropout"):
                    print("Dropout layer found, ignoring it")
                    #if model.dropout_rate ==0:
                    index -= 1
                    continue
                elif str(lp).startswith("z_mean") or str(lp).startswith("z_log_var"):
                    print("Lambda layer found, ignoring it")
                    index -= 1
                    continue
                else:
                    raise ValueError("Only Linear and Sigmoid Layers are supported for now")
        elif ind==1:
            for j in i:
                for lp in j:
                    print(index)
                    index += 1
                    print(lp,index)
                    if str(lp).startswith("Linear"):
                        output.append(render_fc_layer(index, lp))
                    elif str(lp).startswith("Sigmoid"):
                        output.append(render_sigmoid_layer(index, lp,hidden_size=model.encoder.hidden_size))
                    elif str(lp).startswith("Swish"):
                        output.append(render_swish_layer(index, lp,hidden_size=model.encoder.hidden_size))
                    elif str(lp).startswith("Dropout"):
                        print("Dropout layer found, ignoring it")
                        #if model.dropout_rate ==0:
                        index -= 1
                        continue
                    elif str(lp).startswith("z_mean") or str(lp).startswith("z_log_var"):
                        print("Lambda layer found, ignoring it")
                        index -= 1
                        continue
                    else:
                        raise ValueError("Only Linear and Sigmoid Layers are supported for now")
        else:
            raise ValueError("Something is wrong")

    return ''.join(output)

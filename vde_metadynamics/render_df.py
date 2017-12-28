#!/bin/env python
from jinja2 import Template
import numpy as np

plumed_dist_template = Template("DISTANCE ATOMS={{atoms}} LABEL={{label}} ")
plumed_torsion_template = Template("TORSION ATOMS={{atoms}} LABEL={{label}} ")
plumed_angle_template = Template("ANGLE ATOMS={{atoms}} LABEL={{label}} ")
plumed_rmsd_template = Template("RMSD REFERENCE={{loc}} TYPE=OPTIMAL LABEL={{label}} ")
plumed_min_dist_template = Template("DISTANCES GROUPA={{group_a}} GROUPB={{group_b}} MIN={BETA={{beta}}} LABEL={{label}}")

plumed_matheval_template = Template("MATHEVAL ARG={{arg}} FUNC={{func}} LABEL={{label}} PERIODIC={{periodic}} ")

plumed_combine_template = Template("COMBINE LABEL={{label}} ARG={{arg}} COEFFICIENTS={{coefficients}} "+\
                                    "PERIODIC={{periodic}} ")

_SUPPORTED_FEATS=["Contact","Dihedral","AlphaAngle","Angle","Kappa"]

def create_torsion_label(inds, label):
    #t: TORSION ATOMS=inds
    return plumed_torsion_template.render(atoms=','.join(map(str, inds)), label=label) +"\n"

def create_angle_label(inds, label):
    #t: ANGLE ATOMS=inds
    return plumed_angle_template.render(atoms=','.join(map(str, inds)), label=label) +"\n"

def create_distance_label(inds, label):
    return plumed_dist_template.render(atoms=','.join(map(str, inds)), label=label) + "\n"

def create_min_dist_label(group_a,group_b,beta,label):
    return plumed_min_dist_template.render(group_a=','.join(map(str, group_a)),
                                           group_b=','.join(map(str, group_b)),
                                           beta=beta,
                                           label=label)+ "\n"

def create_rmsd_label(loc, label):
    return plumed_rmsd_template.render(loc=loc , label=label) + "\n"



def create_feature(argument, func, label, feature_mean=None, feature_scale=None, offset=None,**kwargs):
    arg = argument
    # if feature_scale is not None and feature_mean is not None:
    #     x = "((x-%s)/%s)"%(feature_mean, feature_scale)
    # else:
    #     x="x"
    x="x"
    if func is None:
        if feature_scale is not None and feature_mean is not None:
            f ="(%s-%s)/%s"%(x,feature_mean, feature_scale)
        else:
            f ="%s"%(x)

    elif func=="min":
        if feature_scale is not None and feature_mean is not None:
            f ="(%s-%s)/%s"%(x,feature_mean, feature_scale,)
        else:
            f ="%s"%(x)
    elif func=="exp":
        if feature_scale is not None and feature_mean is not None:
            f ="(%s(-(%s)^2/(2*%s^2)))-%s)/%s"%(func, x,kwargs.pop("sigma"),
                                                   feature_mean, feature_scale)
        else:
            f = "%s(-(%s)^2/(2*%s^2))"%(func, x, kwargs.pop("sigma"))

    elif func in ["sin","cos"]:
        if feature_scale is not None and feature_mean is not None:
            f = "(%s(%s)-%s)/%s"%(func,x,feature_mean, feature_scale)
        else:
            f = "%s(%s)"%(func,x)

    else:
        raise ValueError("Can't find function")

    if offset is not None:
        f += "-%s"%offset

    return plumed_matheval_template.render(arg=arg, func=f,\
                                           label=label,periodic="NO")



def get_feature_function(df, feature_index):
    possibles = globals().copy()
    possibles.update(locals())
    if df.featurizer[feature_index] == "Contact" and len(df.atominds[feature_index][0])==1:
        func = possibles.get("create_distance_label")
    elif df.featurizer[feature_index] == "Contact" and len(df.atominds[feature_index][0])>1:
        func = possibles.get("create_min_dist_label")
    elif df.featurizer[feature_index] == "LandMarkFeaturizer":
        func = possibles.get("create_rmsd_label")
    elif df.featurizer[feature_index] in ["Kappa","Angle"]:
        func = possibles.get("create_angle_label")
    else:
        func = possibles.get("create_torsion_label")
    return func

def get_feature_transform(df, feature_index):
    possibles = globals().copy()
    possibles.update(locals())
    if df.featurizer[feature_index] == "Contact" and len(df.atominds[feature_index][0])==1:
        func = None
    elif df.featurizer[feature_index] == "Contact" and len(df.atominds[feature_index][0])>1:
        func = "min"
    elif df.featurizer[feature_index] == "LandMarkFeaturizer":
        func = "exp"
        sigma =  df.otherinfo[feature_index]
    else:
        func = df.otherinfo[feature_index]
    return func


def render_atomic_feats(df,inds):
    output = []
    if not set(df.featurizer).issubset(set(_SUPPORTED_FEATS)):
        raise ValueError("Sorry only contact, landmark, and dihedral featuizers\
                         are supported for now")
    possibles = globals().copy()
    possibles.update(locals())

    already_done_list = []

    for j in df.iloc[inds].iterrows():
        feature_index = j[0]
        atominds = np.array(j[1]["atominds"])
        resids = j[1]["resids"]
        feat = j[1]["featuregroup"]
        func = get_feature_function(df, feature_index)
        feat_label = feat+"_%s"%'_'.join(map(str,resids))

        if feat_label not in already_done_list:
            #mdtraj is 0 indexed and plumed is 1 indexed
            if  df.featurizer[feature_index] == "Contact" and len(df.atominds[feature_index][0])==1:
                output.append(func(inds=[np.array(atominds[0][0])+1,
                                         np.array(atominds[1][0])+1],
                                   label=feat_label))
            elif  df.featurizer[feature_index] == "Contact" and len(df.atominds[feature_index][0])>1:
                output.append(func(group_a=np.array(atominds[0])+1,
                                   group_b=np.array(atominds[1])+1,
                                   beta=df.otherinfo[feature_index] ,
                                   label=feat_label))
            else:
                output.append(func(atominds + 1 , feat_label))
            output.append("\n")
            already_done_list.append(feat_label)

    return ''.join(output)

def render_df(df, nrm = None, inds=None, tica_mdl=None, output_label_prefix="f"):
    output = []

    if not set(df.featurizer).issubset(set(_SUPPORTED_FEATS)):
        raise ValueError("Sorry only contact, landmark, and dihedral featuizers\
                         are supported for now")

    if inds is None:
        inds = range(len(df))
    raw_feats = render_atomic_feats(df, inds)
    output.append(raw_feats)

    for j in df.iloc[inds].iterrows():
        feature_index = j[0]
        atominds = j[1]["atominds"]
        feat = j[1]["featuregroup"]
        resids = j[1]["resids"]
        feat = j[1]["featuregroup"]

        label = "%s0_%d"%(output_label_prefix, feature_index)

        func = get_feature_transform(df, feature_index,)
        if df.featurizer[feature_index] == "Contact" and len(df.atominds[feature_index][0])>1:
            feat_label = feat+"_%s"%'_'.join(map(str,resids))+".min"
        else:
            feat_label = feat+"_%s"%'_'.join(map(str,resids))
        sigma = None
        if nrm is not None:
            if hasattr(nrm, "center_"):
                nrm.mean_ = nrm.center_
        if tica_mdl and nrm:
            output.append(create_feature(argument=feat_label,\
                                             func=func,
                                             label=label,
                                             feature_mean = nrm.mean_[feature_index],
                                             feature_scale = nrm.scale_[feature_index],
                                             offset = tica_mdl.means_[feature_index]
                                         ) +"\n")
        elif nrm:
            output.append(create_feature(argument=feat_label,\
                                             func=func,
                                             label=label,
                                             feature_mean = nrm.mean_[feature_index],
                                             feature_scale = nrm.scale_[feature_index],
                                         ) +"\n")
        elif tica_mdl:
            output.append(create_feature(argument=feat_label,\
                                             func=func,
                                             label=label,
                                             offset = tica_mdl.means_[feature_index]
                                         ) +"\n")
        else:
            output.append(create_feature(argument=feat_label,\
                                             func=func,
                                             label=label,
                                         ) +"\n")

        output.append("\n")

    return ''.join(output)


# Transferable Neural Networks + Molecular dynamics 
![Folding Movie](https://github.com/msultan/vde_metadynamics/blob/master/examples/ww_domain/gtt75.gif)

This repo contains information on how to run enhanced sampling simulations 
for mutant proteins using time-lagged variational autoencoders (Variational dynamics encoders). 
The idea is to run enhanced sampling simulations(such as metadynamics) using the latent
node in a [VDE/time-lagged auto enoders](https://arxiv.org/abs/1711.08576). 

For larger systems, we recommend pre-processing using [tICA](http://docs.markovmodel.org/lecture_tica.html) ,to make 
network training easier, and to create efficient collective variables. 

The repo is divided into 2 sections :

1). vde_metadynamics : This folder contains code that can write all the custom [Plumed](plumed.github.io) scrips for 
enhanced sampling. It is built on top of Feature extraction and dimensionality reduction objects found in 
[MSMBuilder](https://github.com/msmbuilder/msmbuilder) plus the [Plumed library](plumed.github.io) which 
interfaces with the [OpenMM](openmm.org) MD engine.  

2). examples: The examples folder contains the ipython notebooks + 
setup scripts needed to reproduce the main results of the paper. It also contains a step-by-step guide on how to 
generate input files needed for Plumed to able to run Metadynamics using the latent collective variable. 

Unfortunately, the actual trajectories are too large for github but are available from us upon
request. 

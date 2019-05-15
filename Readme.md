
This is an implementation provided by the course staff of MIT 6.888 (Hardware Architecture for Deep Learning - Spring 2019). The repo has some added workloads for experiments we used in our final project.

We noticed some use cases that weren't able to run as stated below:
1. The simulator for single PE couldn't handle 1x1 kernel for convolution so we had to use 2x2 and scale our results accordingly.
2. For the 4x4 PE array, the simulator hangs after the fourth tile for a 2x2 ifmap.
3. The output failed to match the expected values when the input/weight values were greater than one and the biases not carefully constructed to keep the outputs small.

Our custom layer shapes are in workloads/layer_shapes and are labeled gcnn_\*. Our ifmap, weights, biases are all in workloads under names shape_gcnn\*.

We also have our report and poster in the repository as well. 

# ---- ORIGINAL README FOR LAB 4-----

# DNN Architecture Evaluation Infrastructure


This is a configurable infrastructure that aims to achieve automatic evaluations of tradeoff between different architecure designs, workload, and mappings

## System Requirement
- python3  
- jupyter notebook  
- pandas
- matplotlib

<sub> Implementation tested in Linux systems and Windows subsystem for Linux (WSL) </sub>

## Install simulator
In order to run simulations of the designs, you need to first install the simualtor as a python egg:  
<sub> **NOTE**:  `<pip_exec>` should be executables/environment_variables for your preferred python intallation. For example, if you are using  python3, and your evironment variable is probably `pip3`. </sub> 
```
cd tools/nnsim
<pip_exec> install --use -e . 
```
You should see a folder named `nnsim.egg-info` created. That means you have successfully installed the simulator package.

## Run a Sample Evaluation
To run a sample evaluation, please follow the following steps:  
<sub> **NOTE**:  `<python_exec>` should be executables/environment_variables for the python intallation you used to install the simulator. For example, if you are using  python3, and your evironment variable is probably `python3`. </sub> 
```
cd ../..              # navigate to lab home directory if you are still in the nnsim folder
cd scripts     
<python_exec> eval.py ws_PE ../designs/ws_PE/arch_parameters/arch_PE.yaml ../workloads/layer_shapes/shape_tiny.yaml ../designs/ws_PE/mappings/N0_1.yaml ../workloads/bias_data/shape_tiny_bias.npy ../workloads/weights_data/shape_tiny_density_100.npy ../workloads/ifmap_data/shape_tiny_density_100.npy ../designs/ws_PE/stats/ws_PE/stats_tiny_N0_1_dense
```
You should see simulation traces, cycle counts, as well energy breakdown output.  
   
The `eval.py` script takes care of the instantiation of simulator, running simulatioin, and use run-time stats to feed into the estimator for a energy evaluation. In this example, a PE design with architecture parameters specified in `arch_PE.yaml` is running a wokload with:  
   * architecture parameters specified in `../designs/ws_PE/arch_parameters/arch_PE.yaml`
   * layer shape specified in `../workloads/layer_shapes/shape_tiny.yaml` 
   * mapping parameters specified in `../designs/ws_PE/mappings/N0_1.yaml`
   * bias data stored in `../workloads/bias_data/shape_tiny_bias.npy `
   * weights data stored in `../workloads/weights_data/shape_tiny_density_100.npy`
   * ifmap data stored in `../workloads/ifmap_data/shape_tiny_density_100.npy`
   * stats output folder name `../designs/ws_PE/stats/ws_PE/stats_tiny_N0_1_dense`
To make the test runs more neat, the framework is also able to auto search for file names based on the file structure and the design name, therefore, the same eval can also be run as  the following
```
<python_exec> eval.py ws_PE arch_PE.yaml shape_tiny.yaml N0_1.yaml shape_tiny_bias.npy shape_tiny_density_100.npy shape_tiny_density_100.npy stats_tiny_k_2_m_2_n_1_dense

```
<sub> **NOTE**:  in order to use this shorter format, you have to make sure all your input files are in the correct folder </sub> 


In summary, the general format of running the evaluation is as follows:  
   ```
   <python exec> eval.py <design_name> <architecture_params> <layer_shape> <mapping> <bias_data> <weights_data_name> <ifmap_data_name> <stats_folder> 
   ```

   
   
## Top Level File Structure
The top level lab folder contains the following top level folders, each will be explained further
```
scripts                  # python scripts for running evaluations on designs
designs                  # repository of designed hardware
workloads                # the avaiable workloads that can be run on different designs
tools                    # simulation framework and estimation framework
sample_outputs           # some sample outputs of the evaluations
```
## Scripts (/scripts folder)
Scripts folder contains scripts that help with automated evaluation process (currently there is only the `eval.py` script)

## Designed Hardware (/designs folder)

In the current infratructure, we provide two fully implemented example hardware designs that can be found in **designs/** folder
   1. Standalone PE design for weight stationary (ws) dataflow
   2. Chip level design for ws dataflow that includes PEs, NoCs, GLBs, etc.

For each design, we have a series of subfloder that contain design related information. We use the standalone PE design as an example
```
ws_PE
   model                # repository for architecture components implementations
   arch_parameters      # repository for files that specify different sets of architecture parameters
   mappings              # repository for mapping parameter files
   testbenches  
      ws_PE                 # repository for files that is related to testing a ws_PE design
```

## Workloads (/workloads folder)

`workloads` folder contains information related to the shape and data of different workloads

```
layer_shapes          #  repository for potential shapes of DNN layers that can be explored
ifmap_data            #  repository for ifmap data of different shapes and densities
weights_data          #  repository for weights data of different shapes and densities
bias_data             #  repository for bias data of different shapes 
```

## Tools (/tools folder)
`tools` folder contains the necessary tools for running evlations. Both tools are fully implementated.
 ```
    nnsim             # repository for simulator related implementations
    estimator         # repository for estimator realted implementations
 ```
## Sample Outputs (/sample_outputs folder)

`sample_outputs` folder, as the name suggests, contains some example outputs we get by running example evaluations








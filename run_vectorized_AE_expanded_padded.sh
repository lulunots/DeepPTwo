#!/bin/bash
#PBS -N xenium_vectorized_ae_expanded_padded
#PBS -k oed
#PBS -l ncpus=4,mem=32gb,ngpus=1,gpuclass=V100,walltime=12:00:00
#PBS -q gpu

MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR

source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
export LD_LIBRARY_PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/lib:$LD_LIBRARY_PATH
echo $PATH

cd /working/lab_quann/louiseN/DeepPT/12AE

python vectorized_model_AE.py AVD_61FEX_expanded_padded --batch-size 512 --epochs 500

#!/bin/bash
#PBS -N xenium_two_slide_pearson
#PBS -k oed
#PBS -l select=1:ncpus=4:mem=32GB,walltime=04:00:00

MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR

source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
export LD_LIBRARY_PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/lib:$LD_LIBRARY_PATH
echo $PATH

python /mnt/backedup/home/louiseN/notebooks/deeppt/preprocessing/two_slide_pipeline/xenium_two_slide_pipeline.py

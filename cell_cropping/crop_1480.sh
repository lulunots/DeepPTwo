#!/bin/bash
#PBS -N cell_crop_1480
#PBS -k oed
#PBS -l select=1:ncpus=2:mem=6GB,walltime=6:00:00

MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR

source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
echo $PATH

slide='1480A'

xenium_folder="/working/lab_quann/louiseN/BC_data/Xenium/metadata/${slide}/he_align/"
output="/working/lab_quann/louiseN/benchmark/deeppt/segmented/${slide}"

script_loc='/mnt/backedup/home/louiseN/notebooks/deeppt/preprocessing'

python3 ${script_loc}/crop_per_cell.py "$xenium_folder" "$output"

#!/bin/bash
#PBS -N expand_pad_5626_batch
#PBS -k oed
#PBS -l select=1:ncpus=12:mem=7GB,walltime=10:00:00
MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR
source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
echo $PATH

slide='5626A'
squaresize=224
script_loc='/mnt/backedup/home/louiseN/notebooks/deeppt/preprocessing'
input_folder="/working/lab_quann/louiseN/benchmark/deeppt/segmented/${slide}"
outloc="/working/lab_quann/louiseN/benchmark/deeppt/expanded_padded/try2/${slide}"

python3 ${script_loc}/batch_expand_and_pad.py "$input_folder" "$squaresize" "$outloc" \
    --processes 12 \
    --interpolation cubic \
    -v
#!/bin/bash
#PBS -N cropped_cells_pad_4851_batch
#PBS -k oed
#PBS -l select=1:ncpus=12:mem=7GB,walltime=06:00:00
MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR
source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
echo $PATH

slide='4851A'
squaresize=224
script_loc='/mnt/backedup/home/louiseN/notebooks/deeppt/preprocessing'
input_folder="/working/lab_quann/louiseN/benchmark/deeppt/segmented/${slide}"
outloc="/working/lab_quann/louiseN/benchmark/deeppt/padded/try2/${slide}"

python3 ${script_loc}/batch_pad.py "$input_folder" "$squaresize" "$outloc" \
    --processes 12 \
    -v
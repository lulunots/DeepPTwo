#!/bin/bash
#PBS -N xenium_realign_variant
#PBS -k oed
#PBS -l select=1:ncpus=2:mem=16GB,walltime=02:00:00

VARIANT="${VARIANT:-expanded_padded}"

MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR

source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
export LD_LIBRARY_PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/lib:$LD_LIBRARY_PATH
echo $PATH
echo "variant: $VARIANT"

python /mnt/backedup/home/louiseN/notebooks/deeppt/preprocessing/two_slide_pipeline/xenium_realign_and_zscore_variant.py "$VARIANT"

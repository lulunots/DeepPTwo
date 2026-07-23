#!/bin/bash
#PBS -N xenium_collect_features
#PBS -k oed
#PBS -l select=1:ncpus=4:mem=32GB,walltime=04:00:00

# Pass which dataset variant to collect via: qsub -v VARIANT=padded run_xenium_collect_features.sh
# Defaults to expanded_padded if not specified.
VARIANT="${VARIANT:-expanded_padded}"

MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR

source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
export LD_LIBRARY_PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/lib:$LD_LIBRARY_PATH
echo $PATH
echo "variant: $VARIANT"

python /mnt/backedup/home/louiseN/notebooks/deeppt/preprocessing/two_slide_pipeline/xenium_collect_features.py "$VARIANT"

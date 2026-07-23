#!/bin/bash
#PBS -N deeppt_train_vec
#PBS -k oed
#PBS -l ncpus=4,mem=32gb,ngpus=1,gpuclass=V100,walltime=24:00:00
#PBS -q gpu
#PBS -J 0-7

# Pass which variant to train via: qsub -v VARIANT=padded run_vectorized_deeppt_train.sh
VARIANT="${VARIANT:-expanded_padded}"
PROJECT="AVD_61FEX_${VARIANT}"

IK_FOLD=$((PBS_ARRAY_INDEX / 4))
GENE_BATCH=$((PBS_ARRAY_INDEX % 4))
I_GENE_STEP=56
I_GENE_MIN=$((GENE_BATCH * I_GENE_STEP))
IL_FOLD=0

echo "variant=$VARIANT, project=$PROJECT, PBS_ARRAY_INDEX=$PBS_ARRAY_INDEX -> ik_fold=$IK_FOLD, i_gene_min=$I_GENE_MIN, i_gene_step=$I_GENE_STEP"

MY_DIR=/mnt/backedup/home/louiseN
cd $MY_DIR

source activate /working/lab_quann/louiseN/miniconda3/envs/deeppt
export PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/bin/:$PATH
export LD_LIBRARY_PATH=/working/lab_quann/louiseN/miniconda3/envs/deeppt/lib:$LD_LIBRARY_PATH
echo $PATH

cd /working/lab_quann/louiseN/DeepPT/13DeepPT_train

python -u vectorized_1main_train.py $PROJECT $IK_FOLD $IL_FOLD $I_GENE_MIN $I_GENE_STEP

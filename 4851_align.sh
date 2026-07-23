#!/bin/bash
#PBS -N xenium_he_align_4851
#PBS -l select=1:ncpus=8:mem=56GB
#PBS -l walltime=2:00:00
#PBS -j oe
#PBS -o xenium_he_align.log

cd "$PBS_O_WORKDIR"

module load apptainer/1.4.1

SIF=/working/lab_quann/louiseN/BC_data/Xenium/metadata/xenium_he_pipeline.sif

apptainer run --bind /mnt/lustre:/mnt/lustre "$SIF" \
  --input /mnt/lustre/working/lab_quann/louiseN/BC_data/Xenium/metadata/4851A \
  --output /mnt/lustre/working/lab_quann/louiseN/BC_data/Xenium/metadata/4851A/he_align \
  --he /mnt/lustre/working/lab_quann/louiseN/BC_data/Xenium/metadata/4851A/HE.ome.tif \
  --matrix /mnt/lustre/working/lab_quann/louiseN/BC_data/Xenium/metadata/4851A/HE_alignment_files/matrix.csv \
  --keypoints /mnt/lustre/working/lab_quann/louiseN/BC_data/Xenium/metadata/4851A/HE_alignment_files/keypoints.csv \
  --max-non-rigid 10000 --reg-level 2 --morph-level 1 --qv-min 20

#!/bin/bash

# Run within BIDS code/ directory:
# sbatch slurm_create_group_mask.sh

# Set partition
#SBATCH --partition=standard

# How long is job (in minutes)?
#SBATCH --time=240

# How much memory to allocate (in MB)?
#SBATCH --cpus-per-task=1 --mem-per-cpu=12000

# Name of jobs?
#SBATCH --job-name=create_group_mask

# Where to output log files?
#SBATCH --output='../derivatives/logs/CreateGroupMask-%A_%a.log'

# Remove modules because Singularity shouldn't need them
echo "Purging modules"
module purge

# Load AFNI module
echo "Loading AFNI module"
module load afni
afni --version

# Load conda environment
source /optnfs/common/miniconda3/etc/profile.d/conda.sh
conda activate narratives

# Print job submission info
echo "Slurm job ID: " $SLURM_JOB_ID
date

source ./analysis_parameters.sh

# Run group level contrasts of each regressor
python ./run_create_group_mask.py "$tasks"
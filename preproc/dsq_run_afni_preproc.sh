#!/bin/bash
#SBATCH --account=turk-browne
#SBATCH --time=3:00:00
#SBATCH --cpus-per-task=1 --mem-per-cpu=8G
#SBATCH --job-name=dsq_3dTproject
#SBATCH --array 371,381,395,405,439,553,591,595,611,659,667,701
#SBATCH --output=/gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log/%A_%a_3dTproject.o

echo "Purging modules"
module purge

# Load AFNI module
echo "Loading AFNI module AFNI/2023.0.07"
module load AFNI/2023.0.07
module load miniconda
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/hbn/joblists/joblist_afni_preproc.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log/


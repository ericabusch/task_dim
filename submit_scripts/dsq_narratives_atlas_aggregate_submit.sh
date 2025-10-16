#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-11
#SBATCH --job-name hbn_aggregate_all_tasks
#SBATCH --mail-type all
#SBATCH --time=20:00
#SBATCH --partition=psych_scavenge
#SBATCH --account=turk-browne


# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda
# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/narratives_atlas_aggregate_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


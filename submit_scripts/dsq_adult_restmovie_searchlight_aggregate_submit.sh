#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-14
#SBATCH --job-name adult_restmovie_aggregate_all_tasks
#SBATCH --mail-type all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda
# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/adult_restmovie_searchlight_aggregate_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


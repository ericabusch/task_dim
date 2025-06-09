#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 5,11,17,23,29,35,41,47,53,59,65,71-80,86-95,101-105,111-115#0-120
#SBATCH --job-name hbn_aggregate_all_tasks
#SBATCH --mail-type all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/hbn_aggregate_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


#!/bin/bash
#SBATCH --output dsq-narratives_searchlight_isc_joblist-%A_%3a-%N.out
#SBATCH --array 0-159
#SBATCH --job-name narratives_isc_all_tasks

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/narratives_searchlight_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


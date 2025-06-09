#!/bin/bash
#SBATCH --output log/%A_%3a-%N.out
#SBATCH --array 0-159
#SBATCH --job-name narratives_ide_all_tasks
#SBATCH -t 24:00:00 
#SBATCH --partition=psych_day
#SBATCH --account=turk-browne
#SBATCH --mem-per-cpu 20G  

# Set up the environment
module load miniconda
conda activate dim_env

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/narratives_atlas_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/log


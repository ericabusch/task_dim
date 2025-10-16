#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array 0-1086
#SBATCH --job-name hbn_ide_all_tasks
#SBATCH --mail-type all
#SBATCH --partition=psych_day
#SBATCH -n 1
#SBATCH --mem-per-cpu=4G
#SBATCH -t 6:00:00

# Set up the environment
module load miniconda
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/hbn_atlas_ide_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


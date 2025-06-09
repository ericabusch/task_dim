#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-154
#SBATCH --job-name partlycloudy_isc_all_tasks
#SBATCH -p psych_week
#SBATCH -t 72:00:00
#SBATCH --mem-per-cpu 8G        
#SBATCH -n 8 
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/partlycloudy_searchlight_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


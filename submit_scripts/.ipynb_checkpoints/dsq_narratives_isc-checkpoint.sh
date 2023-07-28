#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array 1-179
#SBATCH -p psych_day,psych_week
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 40G        
#SBATCH -n 4  
#SBATCH --mail-type=all
#SBATCH --job-name dsq-narratives-isc

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/narratives_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/log

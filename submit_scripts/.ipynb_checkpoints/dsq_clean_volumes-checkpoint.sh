#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array 3-5#0-29
#SBATCH -p psych_day 
#SBATCH -t 6:00:00
#SBATCH --mem-per-cpu 30G        
#SBATCH -n 1  
#SBATCH --mail-type=all
#SBATCH --job-name dsq-clean

# Set up the environment
module load miniconda
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/cnm_clean_data.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log

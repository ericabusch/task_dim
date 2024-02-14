#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array 135-359
#SBATCH -p psych_week,psych_day
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 18G        
#SBATCH -n 8 
#SBATCH --mail-type=all
#SBATCH --job-name dsq-narratives-dse

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/narratives_delta_dse_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/log

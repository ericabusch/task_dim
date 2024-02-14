#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array 0-14
#SBATCH -p psych_day
#SBATCH -t 6:00:00
#SBATCH --mem-per-cpu 10G        
#SBATCH -n 1
#SBATCH --mail-type=all
#SBATCH --job-name dsq-task-comparisons

# Set up the environment
module load miniconda
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/task_comparison_visualize_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log

#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 1,44,59,73,97
#SBATCH -p psych_day
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 30G        
#SBATCH -n 16
#SBATCH --mail-type=all
#SBATCH --job-name dsq-sl

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/narratives_dim_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/log

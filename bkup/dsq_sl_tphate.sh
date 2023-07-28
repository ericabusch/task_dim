#!/bin/bash
#SBATCH --output log/%A_%a.out
#SBATCH --array 0-233
#SBATCH -c 1 -n 16 -N 1 -t 2:00:00 --mem-per-cpu 500M
#SBATCH --partition=psych_day --mail-type ALL 
#SBATCH --job-name dsq-sl_tphate

module load miniconda 
source activate tphate_env

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/log

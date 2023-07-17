#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-51
#SBATCH -p psych_day
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 8G        
#SBATCH -n 8 -N 1         
#SBATCH --mail-type=all
#SBATCH --job-name dsq-sl

# Set up the environment
module load miniconda
module load OpenMPI
conda activate tphate_env


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/vol_sl_tphate_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/log

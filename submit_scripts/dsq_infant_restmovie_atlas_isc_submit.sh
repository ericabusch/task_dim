#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-21,23-24,26-27,29,34-38,42,46-53#0-53
#SBATCH --job-name infant_restmovie_isc_all_tasks
#SBATCH -p psych_day,psych_week
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 20G        
#SBATCH -n 2
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/infant_restmovie_atlas_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


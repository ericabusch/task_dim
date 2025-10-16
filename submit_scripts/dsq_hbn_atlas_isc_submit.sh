#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-528
#SBATCH --job-name hbn_isc_all_tasks
#SBATCH --mail-type all
#SBATCH -n 1
#SBATCH --mem-per-cpu=5G
#SBATCH -t 3:00:00

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/hbn_atlas_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log


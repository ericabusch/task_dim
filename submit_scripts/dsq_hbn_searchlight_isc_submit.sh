#!/bin/bash
#SBATCH --output log/%A_%3a-%N.out
#SBATCH --array 0-153
#SBATCH --job-name hbn_isc_all_tasks
#SBATCH --mem-per-cpu 10G        
#SBATCH -n 4  
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/hbn_searchlight_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


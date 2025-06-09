#!/bin/bash
#SBATCH --output log/dsq-cneuromod_searchlight_ide_joblist-%A_%2a-%N.out
#SBATCH --array 0-68
#SBATCH --job-name cneuromod_ide_all_tasks

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/cneuromod_searchlight_ide_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


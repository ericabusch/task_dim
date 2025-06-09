#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-153
#SBATCH --job-name partlycloudy_ide_all_tasks
#SBATCH -t 6:00:00
#SBATCH --mem-per-cpu 10G        
#SBATCH -n 1 
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/partlycloudy_atlas_ide_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


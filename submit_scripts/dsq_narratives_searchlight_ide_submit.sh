#!/bin/bash
#SBATCH --output log/%A_%2a-%N.out
#SBATCH --array 0-159
#SBATCH --job-name narratives_ide_searchlight
#SBATCH -p psych_day
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 10G        
#SBATCH -n 6  
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/narratives_searchlight_ide_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array 8-159
#SBATCH -p psych_day
#SBATCH -t 6:00:00
#SBATCH --mem-per-cpu 10G        
#SBATCH -n 2 
#SBATCH --mail-type=all
#SBATCH --job-name dsq-narr-ide-atlas

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/atlas_narratives_ide_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log

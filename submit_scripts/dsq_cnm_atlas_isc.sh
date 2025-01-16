#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array 0-26
#SBATCH -p psych_day
#SBATCH -t 6:00:00
#SBATCH --mem-per-cpu 9G        
#SBATCH -n 2 
#SBATCH --mail-type=all
#SBATCH --job-name dsq-cnm-isc-atlas

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/atlas_cnm_isc_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log

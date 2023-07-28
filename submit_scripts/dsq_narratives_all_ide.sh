#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log/%A_%3a.out
#SBATCH --array  0,2,4,6,8,10,12,14,16,18,22,24,26,28,30,32,34,36,38,40,42,44,46,48,50,52,54,56,58,60,62,64,66,68,70,72,74,76,78,80,82,84,86,88,90,92,94,96,98,100,102,104,141-179
#SBATCH -p psych_week
#SBATCH -t 72:00:00
#SBATCH --mem-per-cpu 15G        
#SBATCH -n 8  
#SBATCH --mail-type=all
#SBATCH --job-name dsq-narr-ide

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/narratives_all_ide_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log

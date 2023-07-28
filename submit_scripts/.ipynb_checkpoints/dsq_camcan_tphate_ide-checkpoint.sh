#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 0-350
#SBATCH -p psych_day,psych_week
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 6G        
#SBATCH -n 8  
#SBATCH --mail-type=all
#SBATCH --job-name dsq-camcan-tphate-ide

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda


# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/joblists/camcan_tphate_optt_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/submit_scripts/log

#!/bin/bash
#SBATCH --output log/%A_%3a.out
#SBATCH --array 94,111,140,145,162,219,239,241,249,273,277,294,299,321,366,369,382-383,385,391,401,446,452,489,510,519-520,532,541,547,558,638-1227#0-1227
#SBATCH --job-name hbn_ide_all_tasks
#SBATCH --mail-type all
#SBATCH --partition=psych_day,psych_week
#SBATCH -n 1
#SBATCH --mem-per-cpu=4G
#SBATCH -t 24:00:00

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists/hbn_atlas_ide_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim


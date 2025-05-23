#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log/%A_%4a.txt
#SBATCH --array 51-100
#SBATCH --partition=scavenge
#SBATCH --requeue
#SBATCH --mail-type=all
#SBATCH --job-name dsq-hbn_fmriprep_joblist
#SBATCH --time=1- -N 1 --mem-per-cpu=2GB --ntasks-per-node=16
#SBATCH --dependency=afterany:28386557

# Clear out the working directory

rm -rf /gpfs/milgram/scratch60/turk-browne/elb77/workdir3/20250520*

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/hbn/joblists/joblist_both_tasks_all.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log


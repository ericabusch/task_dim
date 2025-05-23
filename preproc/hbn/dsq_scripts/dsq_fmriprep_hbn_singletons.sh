#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log/%A_%4a_singleton.txt
#SBATCH --array 101-200%10
#SBATCH --partition=scavenge
#SBATCH --requeue
#SBATCH --mail-type=all
#SBATCH --job-name dsq_fmriprep_hbn_chunk
#SBATCH --time=6:00:00 -N 1 --mem-per-cpu=2GB --ntasks-per-node=16
#SBATCH --dependency=singleton

# Remove working directories / files
rm -rf /gpfs/milgram/scratch60/turk-browne/elb77/workdir3/*
rm -rf /gpfs/milgram/project/casey/elb77/HBN_Prep/sourcedata/freesurfer/*/scripts

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/hbn/joblists/joblist_both_tasks_singleton.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log


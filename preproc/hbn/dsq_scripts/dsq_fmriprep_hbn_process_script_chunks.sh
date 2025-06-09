#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log/%A_%3a_proc.txt
#SBATCH --array 200-458%20
#SBATCH --partition=scavenge
#SBATCH --requeue
#SBATCH --mail-type=all
#SBATCH --job-name dsq_fmriprep_hbn_chunk
#SBATCH --time=4:00:00 -N 1 --mem-per-cpu=2GB --ntasks-per-node=16

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/hbn/joblists/process_script_joblist_fmriprep.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log


#!/bin/bash
#SBATCH --output /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log/%A_%1a-dsq_fmriprep.txt
#SBATCH --array 0-3
#SBATCH --job-name dsq-hbn_fmriprep_debug_joblist
#SBATCH --partition=psych_week --time=3-00:00:00 --nodes=1 --ntasks-per-node=1 --ntasks=1 --cpus-per-task=8 --mem-per-cpu=4



# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/hbn/joblists/hbn_fmriprep_debug_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/preproc/log/dsq_fmriprep


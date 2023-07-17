#!/bin/bash
#SBATCH --output log/%A_%2a.out
#SBATCH --array 0-51
#SBATCH -c 1 -n 16 -N 1 -t 24:00:00
#SBATCH --mail-type ALL 
#SBATCH --job-name dsq-sl_benchmark
#SBATCH --partition=psych_day,day,psych_week

module load miniconda 
source activate /gpfs/milgram/project/turk-browne/users/elb77/conda_envs/py3

# DO NOT EDIT LINE BELOW
/gpfs/milgram/apps/hpc.rhel7/software/dSQ/1.05/dSQBatch.py --job-file /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/sl_benchmarks_joblist.txt --status-dir /gpfs/milgram/pi/turk-browne/users/elb77/task_dim/log

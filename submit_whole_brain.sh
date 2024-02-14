#!/bin/bash
#SBATCH --output log/%A.o
#SBATCH --job-name wb
#SBATCH --mem-per-cpu 20G -t 24:00:00 -n 1 -c 1
#SBATCH --mail-type ALL
#SBATCH --partition=psych_day
#SBATCH --account=turk-browne

# module load miniconda
# source activate /gpfs/milgram/project/casey/elb77/conda_envs/tphate_env 

python -u whole_brain_dim.py -d $1

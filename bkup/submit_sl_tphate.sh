#!/bin/bash
#SBATCH --output log/%A.o
#SBATCH --job-name sltphate_forrest
#SBATCH -n 1 -c 16 --mem-per-cpu 5G -t 24:00:00 
#SBATCH --mail-type ALL  --account=turk-browne
#SBATCH --partition=psych_day,day,psych_week

source activate /gpfs/milgram/project/turk-browne/users/elb77/conda_envs/py3
echo $1 $2
python -u sl_tphate.py $1 $2
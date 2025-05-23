#!/bin/bash
#SBATCH --output log/%j_pull_data.out
#SBATCH --job-name pull_forrest_datalad
#SBATCH --ntasks=8
#SBATCH -t 24:00:00 
#SBATCH --mem-per-cpu 8G
#SBATCH --partition=psych_day
#SBATCH --account=turk-browne
#SBATCH --mail-type ALL

module load miniconda
source activate ~/miniconda3/

OUTDIR=/gpfs/milgram/scratch60/turk-browne/elb77/Narratives
cd $OUTDIR
datalad install ///labs/hasson/narratives
cd narratives
datalad install code
datalad get code
python -u /gpfs/milgram/project/turk-browne/users/elb77/task_dim/pull_narratives_datalad_specific.py
echo Done

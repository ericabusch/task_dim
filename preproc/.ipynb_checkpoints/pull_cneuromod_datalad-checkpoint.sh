#!/bin/bash
#SBATCH --output log/%j_pull_data.out
#SBATCH --job-name pull_cneuromod_datalad
#SBATCH --ntasks=8
#SBATCH -t 24:00:00 
#SBATCH --mem-per-cpu 8G
#SBATCH --partition=psych_day
#SBATCH --account=turk-browne
#SBATCH --mail-type ALL

module load miniconda
source activate ~/miniconda3/
eval "$(ssh-agent -s)"

OUTDIR=/gpfs/milgram/scratch60/turk-browne/elb77/cneuromod
# mkdir $OUTDIR
cd $OUTDIR
#datalad install -r git@github.com:courtois-neuromod/cneuromod.processed.git
cd cneuromod.processed
# echo "finished datalad install"
# # only going to download friends s01e02*
TASK="s01e02"
datalad get fmriprep/friends/sub-*/ses-001/func/*${TASK}*space-MNI152NLin2009cAsym_*
datalad get fmriprep/friends/sub-*/ses-001/func/*${TASK}*desc-confounds_timeseries*
datalad get fmriprep/friends/sub-*/ses-001/func/*${TASK}*_events.tsv
echo "got ${TASK}"

# TASKS=("motor","restingstate","social","wm","gambling","emotion","language","relational")
# for T in "${TASKS[@]}"
# do 
# 	datalad get "fmriprep/hcptrt/sub-*/ses-001/func/*${T}*run-1*space-MNI152NLin2009cAsym_*"
# 	datalad get "fmriprep/hcptrt/sub-*/ses-001/func/*${T}*run-1*desc-confounds_timeseries_*"
# 	datalad get "fmriprep/hcptrt/sub-*/ses-001/func/*${T}*run-1*_events.tsv*"
# 	echo "Finished ${T} ses 1"
# 	datalad get "fmriprep/hcptrt/sub-*/ses-002/func/*${T}*run-1*space-MNI152NLin2009cAsym_*"
# 	datalad get "fmriprep/hcptrt/sub-*/ses-002/func/*${T}*run-1*desc-confounds_timeseries_*"
# 	datalad get "fmriprep/hcptrt/sub-*/ses-002/func/*${T}*run-1*_events.tsv*"
# 	echo "Finished ${T} ses 2"
# done

	

# cd narratives
# datalad install code
# datalad get code
# python -u /gpfs/milgram/project/turk-browne/users/elb77/task_dim/pull_narratives_datalad_specific.py
# echo Done

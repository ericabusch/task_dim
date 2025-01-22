#!/bin/bash
#SBATCH --output log/%A_create_task_intersect.o
#SBATCH --job-name create_intersect
#SBATCH --mem-per-cpu 20G -t 24:00:00 -n 1 -c 1
#SBATCH --mail-type ALL
#SBATCH --partition=psych_day
#SBATCH --account=turk-browne

export THIS_PWD=`pwd`

DATASET=$1
TASK=$2
FILE_LIST_FN=${THIS_PWD}/${DATASET}/files_for_intersect_mask_${TASK}.txt 
mkdir -p ${THIS_PWD}/${DATASET}/masks/
MASK_FN=${THIS_PWD}/${DATASET}/masks/${DATASET}_intersect_mask_${TASK}.nii.gz
COUNT_FN=${THIS_PWD}/${DATASET}/masks/${DATASET}_intersect_count_${TASK}.nii.gz
echo "files from: $FILE_LIST_FN"
echo "making: $MASK_FN"

module load miniconda; conda activate env_tda;  python -u create_intersect_mask_file_lists.py -d $DATASET 

bash create_intersect_mask.sh $FILE_LIST_FN $MASK_FN $COUNT_FN
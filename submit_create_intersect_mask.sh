#!/bin/bash
#SBATCH --output log/%A_create_intersect.o
#SBATCH --job-name create_intersect
#SBATCH --mem-per-cpu 20G -t 24:00:00 -n 1 -c 1
#SBATCH --mail-type ALL
#SBATCH --partition=psych_day
#SBATCH --account=turk-browne

export THIS_PWD=`pwd`

DATASET=$1
TASK=$2
FILE_LIST_FN=${THIS_PWD}/${DATASET}/files_for_3mm_intersect_mask.txt 
mkdir -p ${THIS_PWD}/${DATASET}/masks/
MASK_FN=${THIS_PWD}/${DATASET}/masks/${DATASET}_intersect_mask_3mm.nii.gz
COUNT_FN=${THIS_PWD}/${DATASET}/masks/${DATASET}_intersect_count_3mm.nii.gz
echo "$FILE_LIST_FN"
echo "$MASK_FN"

bash create_intersect_mask.sh $FILE_LIST_FN $MASK_FN $COUNT_FN
#!/bin/bash
#SBATCH --output log/%A_create_task_intersect.o
#SBATCH --job-name create_intersect
#SBATCH --mem-per-cpu 20G -t 18:00:00 -n 1 -c 1
#SBATCH --mail-type ALL
#SBATCH --partition=psych_day
#SBATCH --account=turk-browne

export THIS_PWD=`pwd`

DATASET=$1
TASK=$2

for GROUP in 'U_08' 'U_09' 'U_10' 'U_11' 'U_12' 'U_13' 'U_14' 'U_15' 'U_16' 'U_17' 'U_22' ;
do 
    FILE_LIST_FN=${THIS_PWD}/${DATASET}/hbn_files_for_intersect_mask_${GROUP}_${TASK}.txt 
    MASK_FN=${THIS_PWD}/${DATASET}/masks/${DATASET}_intersect_mask_${GROUP}_${TASK}.nii.gz
    COUNT_FN=${THIS_PWD}/${DATASET}/masks/${DATASET}_intersect_count_${GROUP}_${TASK}.nii.gz
    echo "files from: $FILE_LIST_FN"
    echo "making: $MASK_FN"
    bash create_intersect_mask.sh $FILE_LIST_FN $MASK_FN $COUNT_FN
done
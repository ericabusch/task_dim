#!/bin/bash

## Dataset paths
DATASET_NAME=$1
INPUT_DIR=$2
OUTPUT_DIR=$3
PARTICIPANT=$4
TASK=$5

WORK_DIR=/gpfs/milgram/scratch60/turk-browne/elb77/workdir/${DATASET_NAME}/${PARTICIPANT}/${TASK}
mkdir -p ${WORK_DIR}

echo $DATASET_NAME $INPUT_DIR $OUTPUT_DIR $PARTICIPANT $TASK
module load fmriprep
module load FreeSurfer

fmriprep --participant-label ${PARTICIPANT} -t ${TASK} -w ${WORK_DIR} --skip_bids_validation --output-spaces MNI152NLin2009cAsym:res-native --fs-license-file $FREESURFER_HOME/.license
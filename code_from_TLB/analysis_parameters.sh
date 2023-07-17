#!/bin/bash

# This script will be sourced by the slurm analysis scripts
# Use this to change task, subjects, and analysis name of all scripts

tasks=("black" "forgot" "bronx" "piemanpni")

#beta fingerprinting options:
#    - within-across: compute index of similarity to self > similarity to others
#    - within: compute similarity of subjects to themselves across tasks
#    - across: compute similarity of subjects to all other subjects
# ("within-across" "within" "across")
analysis_idxs=("within-across" "within" "across")

# which type of permutation to conduct:
#    - subjects: permute subject label
#    - rois: permute voxels within roi --> this doesn't average over subjects and only makes sense for within
perm="rois"

#contains all of the information on which participants in which task
participants_file='/dartfs/rc/lab/D/DBIC/DBIC/archive/narratives/participants.tsv'

#grab all subjects for each task - add to an overall task list
for task in ${tasks[@]}; do
    task_subs=($(awk -F"\t" '$4~"'${task}'" { print $1 }' ${participants_file}))
    task_sub_list=(${task_sub_list[@]} ${task_subs[@]})
done

# reduce the task sub-list to unique subjects
subjects=($(for sub in "${task_sub_list[@]}"; do echo "${sub}"; done | sort -u))

# #subset of subjects we want to process for the given task
start_subject=1
# max_subjects=2

#if max subjects is not set, set to maximum number possible
if [ -z ${max_subjects+x} ]; then
    max_subjects="${#subjects[@]}"
fi
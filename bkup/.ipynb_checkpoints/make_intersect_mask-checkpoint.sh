#!/bin/bash
#
# Generate intersect mask

dirname=$1 # where to find this data; eg /gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Mickey/preprocessed_standard/nonlinear_alignment/

filematch=$2 # string to match on filename; eg rest_movie_*_functional*_fslmotion*_Only.nii.gz
dataset=$3 # used for labeling this new file; eg Adult_Mickey
echo ${dirname}
files=`ls ${dirname}/${filematch}`

mask_name=./masks/${dataset}_intersect_mask.nii.gz

ppt_num=`echo $files | wc -w`
echo Making $mask_name with $ppt_num participants

# Remove the intersect
rm -f $mask_name

for file in $files
do
    data=$file

    # Take only a single TR
    fslroi $data temp.nii.gz 0 1

    # Merge or create the mask
    if [ -e $mask_name ]
    then
        fslmerge -t $mask_name $mask_name temp.nii.gz
    else
        cp temp.nii.gz $mask_name
    fi
    
done

# Remove intermediate file
rm -f temp.nii.gz

# Average the data across time
fslmaths $mask_name -abs -thr 0 -bin -Tmean -thr 1 -bin $mask_name
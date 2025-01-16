#!/bin/bash
#
# create intersect mask from a file specifying all filenames
module load FSL 
. /gpfs/milgram/apps/hpc.rhel7/software/FSL/6.0.5-centos7_64/etc/fslconf/fsl.sh

volume_filelist=$1 # file with filenames that will be used for making the mask
mask_name=$2 # filename for mask
count_name=$3

echo ${volume_filelist} ${out_filename}
filelist=`cat ${volume_filelist}`
num_files=`echo $filelist | wc -w`
echo Making $mask_name with $num_files files from $volume_filelist

# Remove the intersect
rm -f $mask_name

for file in $filelist
do
    data=$file

    # Take only a single TR
    fslroi $data $count_name 0 1

    # Merge or create the mask
    if [ -e $mask_name ]
    then
        fslmerge -t $mask_name $mask_name $count_name
    else
        cp $count_name $mask_name
    fi
    
done

fslmaths $mask_name -abs -thr 0 -bin -Tmean -thr 1 -bin $mask_name
# mask with MNI
echo averaged and binned


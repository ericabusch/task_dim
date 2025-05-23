#!/bin/bash
#SBATCH --mem-per-cpu 5G -n 2 -c 1 -N 1
#SBATCH --time 10:00:00
#SBATCH --account=turk-browne
#SBATCH --partition=psych_day
#SBATCH --job-name randomise
#SBATCH --output log/%J-randomise.out 
#SBATCH --mail-type=begin
#SBATCH --mail-type=end

# load miniconda & start environment
module load miniconda
module load FSL/6.0.5-centos7_64;
. /gpfs/milgram/apps/hpc.rhel7/software/FSL/6.0.5-centos7_64/etc/fslconf/fsl.sh;
# start environment
conda activate env_tda;
cd /gpfs/milgram/project/turk-browne/users/elb77/task_dim/joblists

input_filelist=$1 # file with filenames that will be used for making the mask
filelist=`cat ${input_filelist}`
num_files=`echo $filelist | wc -w`
echo Running $num_files files from $input_filelist

for file in $filelist
do
    fn=$file
	to_replace='.nii.gz'
	replace_with='randomise_output'
	outfn="${fn/$to_replace/"$replace_with"}"
	randomise -i $fn -o $outfn -1 -T -v 5 
	echo Done $outfn
done
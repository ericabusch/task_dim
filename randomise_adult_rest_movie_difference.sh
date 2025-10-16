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
conda activate env_tda
# start environment
cd /gpfs/milgram/project/turk-browne/users/elb77/task_dim

dirname="adult_restmovie/results/task_comparisons/"

#filelist=("adult_restmovie/results/task_comparisons/rest_mickey_all_subjects.nii.gz" "adult_restmovie/results/task_comparisons/rest_aeronaut_all_subjects.nii.gz")
#echo Running $num_files files
filelist=("adult_restmovie/results/task_comparisons/rest_aeronaut_all_subjects.nii.gz")
for file in $filelist
do
    fn=$file
	to_replace='.nii.gz'
	replace_with='randomise_output'
	outfn="${fn/$to_replace/"$replace_with"}"
	randomise -i $fn -o $outfn -1 -T -v 5 
	echo Done $outfn
done

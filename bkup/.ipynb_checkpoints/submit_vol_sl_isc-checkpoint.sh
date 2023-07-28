#!/usr/bin/env bash
# Input python command to be submitted as a job

#SBATCH --output=log/%j.out
#SBATCH --job-name searchlight_isc
#SBATCH -p psych_day 
#SBATCH -t 24:00:00
#SBATCH --mem-per-cpu 25G        
#SBATCH -n 4    
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

echo $1 $2 $3

# Run the python script
# python -u parcel_tphate.py $1
srun --mpi=pmi2 python -u narratives_vol_searchlight_isc.py $1 $2 $3
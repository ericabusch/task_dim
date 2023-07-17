#!/usr/bin/env bash
# Input python command to be submitted as a job

#SBATCH --output=log/%j.out
#SBATCH --job-name searchlight
#SBATCH -p psych_day 
#SBATCH -t 3:00:00
#SBATCH --mem-per-cpu 10G        
#SBATCH -n 20         
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate tphate_env

echo $1 $2 $3

# FILE=
# if [ -f "$FILE" ]; then
#     echo "$FILE exists."
# else 
#     echo "$FILE does not exist."
# fi

# Run the python script
srun --mpi=pmi2 python -u forrest_vol_searchlight_tphate.py $1 $2 $3

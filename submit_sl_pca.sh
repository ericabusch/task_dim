#!/bin/bash
#SBATCH --output=log/%j.out
#SBATCH --job-name tph_searchlight
#SBATCH -p psych_day 
#SBATCH -t 1:00:00
#SBATCH --mem-per-cpu 10G        
#SBATCH -n 16 -N 1  
#SBATCH --mail-type=all

# Set up the environment
module load miniconda
module load OpenMPI
conda activate env_tda

echo $1 $2 $3
srun --mpi=pmi2 python -u narratives_vol_searchlight_tphate.py $1 $2 $3

#for S in 1 2 3 4 5 6 7 8 9 10 11 12; do for T in REST AERONAUT MICKEY; do for R in 90 99; do sbatch submit_sl_pca.sh $S $T $R; done; done; done
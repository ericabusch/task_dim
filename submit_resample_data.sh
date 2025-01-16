#!/bin/bash
#SBATCH --output log/%A_resample_data.o 
#SBATCH --job-name resample_data
#SBATCH --mem-per-cpu 30G # the total memory for this job will be --mem-per-cpu * --cpus-per-task * ntasks , so be careful!
#SBATCH -t 24:00:00 
#SBATCH --ntasks 1 # number of tasks (MPI workers)
#SBATCH --nodes 1 # number of nodes total; to make sure all jobs are on the same node, set to 1
#SBATCH --cpus-per-task 1 # matches the number of jobs I've requested in the joblib parallel 
#SBATCH --mail-type ALL # i like getting email updates when my jobs start/finish, optional
#SBATCH --partition=psych_day # always use the psych_* ; if you need more than 24h, go to psych_week
#SBATCH --account=turk-browne # what group the job's under; if youre on multple accounts (i am) you should specify , otherwise it'll default

# Set up the environment
module load miniconda
conda activate env_tda # this is my conda env

# modify this
FULL_PATH_TO_SCRIPT='/gpfs/milgram/project/turk-browne/users/elb77/task_dim'

# comes from command line call like
# sbatch submit_resample_data.sh dataset_A
DATASET_NAME=$1

python -u ${FULL_PATH_TO_SCRIPT}/resample_wb_mni_data.py -d ${DATASET_NAME}

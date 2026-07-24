# config for healthy brain network dataset
from os.path import join
import glob
import os
import pandas as pd

NJOBS=16
VERBOSE=True

# check if running on milgram, radev/grace, or local
if 'milgram' in os.uname()[1]:
    ROOT = 'ROOT_PATH'
    SCRATCH_DIR = 'SCRATCH_PATH/task_dim_sandbox'
elif os.path.exists('/gpfs/radev'):
    ROOT = 'ROOT_PATH'
    SCRATCH_DIR = 'SCRATCH_PATH/task_dim_sandbox'
else:
    _repo_dir = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(_repo_dir)
    SCRATCH_DIR = os.path.join(_repo_dir, 'scratch')

TR = 1.450
KNN=5
THRESHOLD=0.9
TRIM=-1
IDE_METHODS = ['TPHATE_DiffOp_IDE','PCA']
# my dataset
MY_PREPROC_HBN=f'{ROOT}/HBN_Prep'
BASE_DIR_HBN = f'{ROOT}/HealthyBrainNetwork/'
RAW_HBN_DIR=f'{ROOT}/HBN/HBN_BIDS'
HBN_INTERSECT_MASK=f'{ROOT}/task_dim/HBN/masks/HBN_intersect_mask.nii.gz'
HBN_OUTDIR = f'{ROOT}/task_dim/HBN'
HBN_RESULTS_DIR = f'{HBN_OUTDIR}/results'
HBN_TASKS = ['rest','movieTP']# 'movieDM', 
HBN_PARTICIPANT_INFO = f'{HBN_OUTDIR}/study-HBN_desc-participants.tsv'
AGE_BINS = [8,9,10,11,12,13,14,15,16,17,22]
BASIC_PARTICIPANT_DF =  f'{HBN_OUTDIR}/basic_cohort_info.csv'
HBN_PARTICIPANT_FMRIPREP = f'{HBN_OUTDIR}/fmriprep_participants.txt'
HBN_AGE_GROUPS=['U_08','U_09','U_10','U_11','U_12','U_13','U_14','U_15','U_16','U_17','U_22']
HBN_AGE_GROUPS_COARSE=['U_08','U_09','U_10','U_11','U_12','U_13','U_14','U_15','U_16','U_17','18_plus']

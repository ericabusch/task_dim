# config for healthy brain network dataset
from os.path import join
import glob
import os
import pandas as pd

NJOBS=16
VERBOSE=True

# check if running on milgram or misha
if 'milgram' in os.uname()[1]:
    ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
    SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
else:
    ROOT = '/gpfs/radev/home/elb77/project/task_dim'
    SCRATCH_DIR = f'/gpfs/radev/scratch60/turk-browne/elb77/task_dim_sandbox'

TR = 1.450
KNN=10
THRESHOLD=0.9
TRIM=-1
IDE_METHODS = ['TPHATE_DiffOp_IDE','PCA']
# my dataset
MY_PREPROC_HBN='/gpfs/milgram/project/casey/elb77/HBN_Prep'
BASE_DIR_HBN = f'//gpfs/milgram/project/turk-browne/projects/HealthyBrainNetwork/'
RAW_HBN_DIR='/gpfs/milgram/scratch60/turk-browne/elb77/HBN/HBN_BIDS'
HBN_INTERSECT_MASK=f'{ROOT}/task_dim/HBN/masks/HBN_intersect_mask.nii.gz'
# HBN_PARTICIPANTS_ORIG = [f.split('/')[-1] for f in glob.glob(f'{DATALAD_DIR_HBN}/*') if os.path.isdir(f)]
HBN_OUTDIR = f'{ROOT}/task_dim/HBN'
HBN_RESULTS_DIR = f'{HBN_OUTDIR}/results'
HBN_TASKS = ['rest','movieTP']# 'movieDM', 
HBN_PARTICIPANT_INFO = f'{HBN_OUTDIR}/study-HBN_desc-participants.tsv'
AGE_BINS = [8,9,10,11,12,13,14,15,16,17,22]
BASIC_PARTICIPANT_DF =  f'{HBN_OUTDIR}/participants.csv'
#HBN_PARTICIPANTS_ALL = pd.read_csv(BASIC_PARTICIPANT_DF).subject_id.values
HBN_PARTICIPANT_FMRIPREP = f'{HBN_OUTDIR}/fmriprep_participants.txt'
HBN_AGE_GROUPS=['U_08','U_09','U_10','U_11','U_12','U_13','U_14','U_15','U_16','U_17','U_22']

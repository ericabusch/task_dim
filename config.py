# Paths and variables specific to the datasets
# elb, 2024
from os.path import *
import numpy as np
import glob
import os

NJOBS=16
VERBOSE=True
ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
KNN=10
THRESHOLD=0.85

#### Adult rest-movie parameters
BASE_DIR_RM='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/'
REST_DIR="/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Rest/preprocessed_standard/nonlinear_alignment/"
AERONAUT_DIR="/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Aeronaut/preprocessed_standard/nonlinear_alignment/"
MICKEY_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Mickey/preprocessed_standard/nonlinear_alignment/'
LK_CARTOON_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/LionKing_Cartoon/preprocessed_standard/nonlinear_alignment/' # appears to be not formatted
LK_LA_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/LionKing_Live/preprocessed_standard/nonlinear_alignment/' # appears to be not formatted
RM_DATA_DIRS={'REST':REST_DIR, 'AERONAUT':AERONAUT_DIR, 'MICKEY':MICKEY_DIR}
RM_TIMEPOINTS={'REST':152, 'AERONAUT':93, 'MICKEY':74, 'LK_CARTOON':93, 'LK_LA':93}
RM_MASKS={K:f'{ROOT}/task_dim/masks/Adult_{K.lower().capitalize()}_intersect_mask.nii.gz' for K in RM_DATA_DIRS.keys()}
RM_SUBJECTS = [f'rest_movie_{i:02d}' for i in [1,2,3,4,5,7,8,9,10,11,12]] # subject 6 does not have mickey
RM_OUTDIR = f'{ROOT}/task_dim/RestMovie'
RM_STRING_MATCH = '*_fslmotion_thr0.2_Only.nii.gz'
RM_INTERSECT_MASK = f'{ROOT}/task_dim/RestMovie/masks/RestMovie_intersect_mask.nii.gz'
RM_RESULTS_DIR = f'{ROOT}/task_dim/RestMovie/results/'
RM_MULTIPLE_FILES = []



### CONFIG FOR REST MOVIE INFANTS 
# TASK NAME = infant_rest_movie
INFANT_SLEEP_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Sleep/preprocessed_standard/nonlinear_alignment/'
AERONAUT_B_RM_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Aeronaut/preprocessed_standard/nonlinear_alignment/'
MICKEY_B_RM_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Mickey/preprocessed_standard/nonlinear_alignment/'
INFANT_AERO_DIR = '/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/Aeronaut/preprocessed_standard/nonlinear_alignment/'
INFANT_MICKEY_DIR = '/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/Mickey/preprocessed_standard/nonlinear_alignment/'
RM_INFANT_OUTDIR = f'{ROOT}/task_dim/InfantRestMovie'
RM_INFANT_DATA_DIRS={'sleep':INFANT_SLEEP_DIR, 'aeronaut':AERONAUT_B_RM_DIR, 'mickey':MICKEY_B_RM_DIR}
RM_INFANT_STRING_MATCH={t:'*_fslmotion_thr0.2_Only.nii.gz' for t in RM_INFANT_DATA_DIRS.keys()}#'aeronaut':'Z','mickey':'Z'}

SLEEP_INFANT_SUBJECTS = ["s0307_1", "s2057_1","s2067_1","s2097_1","s2307_1","s2986_1","s2986_1","s3097_1", "s4107_1", "s5927_1", "s6057_1", "s6057_1", "s7286_2", "s8187_1", "s8687_2", "s9986_1"]

# the ones that were only included in the RM dataset -- use these subjects
AERO_INFANT_RM_SUBSET= ["s0057_1", "s0607_1", "s1607_1", "s2037_1", "s2057_1", "s3097_1", "s3607_1", "s4047_1", "s4607_1", "s5037_1","s6057_1","s6607_1","s6687_1","s7017_1","s7067_1","s8037_1","s8687_1"]
MICKEY_INFANT_RM_SUBSET=["s0307_2","s2307_1","s6687_1","s8187_1","s8687_1"]

# This is the full dataset -- dont use!
MICKEY_INFANT_SUBJECTS = ['s0307_1','s0307_2','s0687_1','s1187_1','s2307_1','s2687_1',
's5187_1','s5687_1','s6607_1','s6687_1','s8187_1','s8607_1','s8687_1']
AERO_INFANT_SUBJECTS = ['s0057_1','s0607_1','s0687_1','s1607_1','s2037_1','s2047_1','s2057_1','s2067_1','s2097_1','s2687_1','s3097_1','s3607_1','s4047_1','s4607_1','s5037_1','s6017_1',
's6057_1','s6607_1','s6687_1','s6687_1','s7017_1','s7057_1','s7067_1','s8037_1','s8077_1','s8687_1','s8687_2','s9057_1']
INFANT_PARTICIPANT_DATA = {'sleep':'/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Sleep/infant_sleep_participants.csv',
 'aeronaut':'/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Aeronaut/infant_aeronaut_participants.csv',
 'mickey':'/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Infant_Mickey/infant_mickey_participants.csv'
 }

SLEEP_INFANT_SUBJECTS_2 = ['s0307_1_1', 's2307_1_1', 's8187_1_4', 's4107_1_1', 's8687_2_2',
       's2057_1_2', 's6057_1_4', 's6057_1_7', 's2067_1_2', 's2097_1_4',
       's3097_1_4', 's3097_1_4', 's5927_1_1', 's9986_1_1', 's9986_1_4',
       's9986_1_5', 's2986_1_1', 's2986_1_2', 's7286_2_2', 's7286_2_3']

# the ones that were only included in the RM dataset -- use these subjects, with repeats
AERO_INFANT_RM_SUBSET_2 = ['s8687_1_3', 's8687_1_4', 's8687_1_5', 's8687_1_7', 's8687_2_1',
       's6687_1_3', 's6687_1_4', 's6687_1_5', 's6687_1_6', 's4607_1_5',
       's6607_1_2', 's0607_1_2', 's1607_1_4', 's3607_1_2', 's2057_1_2',
       's6057_1_1', 's6057_1_2', 's0057_1_3', 's7017_1_1', 's7017_1_2',
       's8037_1_2', 's2037_1_2', 's5037_1_1', 's7067_1_3', 's4047_1_1',
       's3097_1_1']
MICKEY_INFANT_RM_SUBSET_2 =['s0307_2_1', 's0307_2_1', 's8187_1_8', 's2307_1_2', 's2307_1_2',
       's6687_1_1', 's8687_1_2', 's0687_1_2']

RM_INFANT_OVERLAPPING_SUBJECTS = {'mickey_sleep': ['s8187_1','s2307_1'], 
'aeronaut_sleep':['s8687_2','s2057_1','s6057_1','s3097_1'], 
'aeronaut_mickey':['s6687_1','s8687_1']}

INFANT_SUBJECTS_TASKS = {"sleep": SLEEP_INFANT_SUBJECTS_2, 
						 "aeronaut":AERO_INFANT_RM_SUBSET_2, 
						 "mickey":MICKEY_INFANT_RM_SUBSET_2} # all mickey infants saw it twice in a row (148 trs) so just include 74

SLEEP_INFANT_INTERSECT_MASK = f'{RM_INFANT_OUTDIR}/masks/InfantRestMovie_intersect_mask_sleep.nii.gz'
AERONAUT_INFANT_INTERSECT_MASK = f'{RM_INFANT_OUTDIR}/masks/InfantRestMovie_intersect_mask_aeronaut.nii.gz'
MICKEY_INFANT_INTERSECT_MASK = f'{RM_INFANT_OUTDIR}/masks/InfantRestMovie_intersect_mask_mickey.nii.gz'
INFANT_INTERSECT_MASKS = {"sleep":SLEEP_INFANT_INTERSECT_MASK, "aeronaut":AERONAUT_INFANT_INTERSECT_MASK,"mickey": MICKEY_INFANT_INTERSECT_MASK}
RM_INFANT_TIMEPOINTS={'sleep':152, 'aeronaut':93, 'mickey':74}
RM_INFANT_RESULTS_DIR = f'{RM_INFANT_OUTDIR}/results/'
RM_INFANT_MULTIPLE_FILES = {"sleep": {"s2986_1":4, "s3097_1":2, "s6057_1":4, "s7286_2":2, "s9986_1":3}, 
"mickey": {"s0307_2":2, "s2307_1":2},
'aeronaut':{'s1607_1':2, 's6057_1':2, "s6687_1":4, "s7017_1":2, "s8687_1":4}}




### CONFIG INFO FOR NARRATIVES ##
BASE_DIR_NARRATIVES = '/gpfs/milgram/project/turk-browne/projects/Narratives'
NARRATIVES_DATALAD_DIR='/gpfs/milgram/scratch60/turk-browne/elb77/Narratives/narratives'
NARRATIVES_DATA_DIRS = {'black':join(BASE_DIR_NARRATIVES, 'black_3mm'),
                        'piemanpni':join(BASE_DIR_NARRATIVES, 'piemanpni_3mm'), 
                        'bronx':join(BASE_DIR_NARRATIVES, 'bronx_3mm'),
                        'forgot':join(BASE_DIR_NARRATIVES, 'forgot_3mm')}

NARRATIVES_SUBJECTS = [127, 265, 267, 272, 273, 274, 275, 276, 277, 279, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 
291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315]
NARRATIVES_SUBJECTS = [f'sub-{s}' for s in NARRATIVES_SUBJECTS]
exclude = ['sub-309','sub-306','sub-303','sub-305','sub-298']
NARRATIVES_SUBJECTS = [x for x in NARRATIVES_SUBJECTS if x not in exclude]

NARRATIVES_TIMEPOINTS={'black':550, 'bronx':390, 'forgot':574, 'piemanpni':294}
NARRATIVES_OUTDIR = f'{ROOT}/task_dim/Narratives'
NARRATIVES_RESULTS_DIR = f'{ROOT}/task_dim/Narratives/results'
NARRATIVES_INTERSECT_MASK=f'{ROOT}/task_dim/Narratives/masks/Narratives_intersect_mask.nii.gz'

## CONFIG INFO FOR CNEUROMOD
BASE_DIR_CNEUROMOD='/gpfs/milgram/project/turk-browne/projects/CNeuroMod'
CNM_SUBJECTS = [1,3,5]
CNM_SUBJECTS = [f'sub-0{s}' for s in CNM_SUBJECTS]
CNM_DATALAD_DIR = "/gpfs/milgram/scratch60/turk-browne/elb77/cneuromod/cneuromod.processed/fmriprep"
CNM_TASKS = ["motor","restingstate","social","wm","gambling","emotion","language","relational", "s01e04a", "s01e04b"]
CNM_TASK_TO_TASK_TYPE = {'motor':'hcptrt', 'restingstate':'hcptrt','social':'hcptrt','wm':'hcptrt',
'gambling':'hcptrt','emotion':'hcptrt','language':'hcptrt','relational':'hcptrt','s01e04a':'friends','s01e04b':'friends'}
CNM_SESSIONS = ['ses-001','ses-002']
CNM_DATA_DIRS = { K:f'{BASE_DIR_CNEUROMOD}/{K}_3mm_cleaned' for K in CNM_TASKS }
CNM_INTERSECT_MASK=f'{ROOT}/task_dim/Cneuromod/masks/cneuromod_intersect_mask_3mm.nii.gz'
CNM_OUTDIR = f'{ROOT}/task_dim/Cneuromod'
CNM_RESULTS_DIR = f'{CNM_OUTDIR}/results'
CNM_TR = 1.49
# Accounts for multiple runs of the same task
CNM_MULTIPLE_FILES = {"motor": {s:3 for s in CNM_SUBJECTS}, 
"social":{s:3 for s in CNM_SUBJECTS},
"wm": {s:3 for s in CNM_SUBJECTS}, 
"gambling":{s:3 for s in CNM_SUBJECTS}, 
"emotion":{'sub-01':2, 'sub-03':3, 'sub-05':3},
"language":{'sub-01':2, 'sub-03':3, 'sub-05':3},
"relational":{'sub-01':2, 'sub-03':3, 'sub-05':3}}

########################################
BASE_DIR_PARTLY_CLOUDY = '/gpfs/milgram/project/turk-browne/projects/partly_recon'
PC_SUBJECTS = [f'sub-pixar{i:03d}' for i in range(1,156)]
PC_DATA_DIR = f'{BASE_DIR_PARTLY_CLOUDY}/data/resampled_participants/motion_reg/'
PC_INTERSECT_MASK=f'{ROOT}/task_dim/PartlyCloudy/masks/PartlyCloudy_intersect_mask.nii.gz'
PC_OUTDIR = f'{ROOT}/task_dim/PartlyCloudy/'
PC_RESULTS_DIR=f'{PC_OUTDIR}/results'
PC_PARTICIPANT_DF=f'{BASE_DIR_PARTLY_CLOUDY}/participantinfo/participants.csv'
PC_AGE_GROUPS = ['3yo','4yo','5yo','7yo','8-12yo','Adult','all']


#########################################
## CONFIG INFO FOR CAMCAN
BASE_DIR_CAMCAN = '/gpfs/milgram/project/casey/elb77/CamCAN/'
CAMCAN_PREPROC_MIDSTR='cc700/mri/pipeline/release004/data_fMRI/aamod_norm_write_dartel_00001/'
CAMCAN_RAW_MIDSTR='cc700/mri/pipeline/release004/BIDS_20190411/'

CAMCAN_RAW_DIRS = {'MOVIE':join(BASE_DIR_CAMCAN, CAMCAN_RAW_MIDSTR, 'epi_movie'),
                    'REST':join(BASE_DIR_CAMCAN, CAMCAN_RAW_MIDSTR, 'epi_rest'),
                    'SMT': join(BASE_DIR_CAMCAN, CAMCAN_RAW_MIDSTR, 'epi_smt')}
CAMCAN_TASKS = ['MOVIE','REST','SMT']
CAMCAN_DIR_CODE = {"MOVIE":'Movie', 'REST':"Rest", "SMT": "SMT"}

CAMCAN_PARTICIPANT_FILES = {TASK: join(CAMCAN_RAW_DIRS[TASK], 'participants.tsv') for TASK in CAMCAN_TASKS}

CAMCAN_ORGANIZED_DIRS = {'MOVIE': join(BASE_DIR_CAMCAN,'fMRI_organized', 'movie'), 
                        'REST': join(BASE_DIR_CAMCAN,'fMRI_organized', 'rest'),
                        'SMT': join(BASE_DIR_CAMCAN,'fMRI_organized', 'smt')}
CAMCAN_RESULTS_DIR = f'{ROOT}/task_dim/CamCAN/results'

## 
def intersecting_items(dict_of_lists):
    # Initialize intersection result with the first set
    keys = list(dict_of_lists.keys())
    result = dict_of_lists[keys[0]]
    for i, k in enumerate(keys[1:]): 
        v = dict_of_lists[k]
        result = [r for r in result if r in v]
    return result

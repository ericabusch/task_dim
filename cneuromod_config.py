# cneuromod config
import numpy as np
from os.path import join
import os

NJOBS=16
VERBOSE=True

# check if running on milgram, radev/grace, or local
if 'milgram' in os.uname()[1]:
    ROOT = '/gpfs/milgram/project/turk-browne/users/elb77'
    SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
elif os.path.exists('/gpfs/radev'):
    ROOT = '/gpfs/radev/home/elb77/project/task_dim'
    SCRATCH_DIR = '/gpfs/radev/scratch60/turk-browne/elb77/task_dim_sandbox'
else:
    _repo_dir = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(_repo_dir)
    SCRATCH_DIR = os.path.join(_repo_dir, 'scratch')
KNN=5
THRESHOLD=0.9
IDE_METHODS = ['TPHATE_DiffOp_IDE','PHATE_DiffOp_IDE', 'MiND_ML','PCA','MLE','lPCA']


## CONFIG INFO FOR CNEUROMOD
BASE_DIR_CNEUROMOD='/gpfs/milgram/project/turk-browne/projects/CNeuroMod'
CNM_SUBJECTS = [1,3,5]
CNM_SUBJECTS = [f'sub-0{s}' for s in CNM_SUBJECTS]
CNM_DATALAD_DIR = "/gpfs/milgram/scratch60/turk-browne/elb77/cneuromod/cneuromod.processed/fmriprep"
CNM_TASKS = ["motor","restingstate","social","wm","gambling","emotion","language","relational", "s01e04a", "s01e04b"]
CNM_TASK_TO_TASK_TYPE = {'motor':'hcptrt', 
						'restingstate':'hcptrt',
						'social':'hcptrt',
						'wm':'hcptrt',
						'gambling':'hcptrt',
						'emotion':'hcptrt',
						'language':'hcptrt',
						'relational':'hcptrt',
						's01e04a':'friends',
						's01e04b':'friends'}

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
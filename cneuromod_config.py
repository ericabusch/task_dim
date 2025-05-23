# cneuromod config
import numpy as np
from os.path import join

NJOBS=16
VERBOSE=True
ROOT = ''
SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
KNN=5
THRESHOLD=0.9
IDE_METHODS = ['TPHATE_DiffOp_IDE','TPHATE_VNE_IDE', 'PHATE_VNE_IDE','PCA','MLE']

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
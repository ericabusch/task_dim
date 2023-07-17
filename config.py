# Paths and variables specific to the datasets
# erica busch, 2022
from os.path import *
import numpy as np
import glob

NJOBS=16

ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dimension'
RAW_DIR = f'{ROOT}/StudyForrest/studyforrest_bids/derivatives/fmriprep/'
LABELS_DIR = f'{ROOT}/task_dim/labels'
FEATURES_FILE=f'{LABELS_DIR}/forrest_movie_labels_coded_expanded.csv'
RESULTS_DIR = f'{ROOT}/task_dim/results'
PREPROC_DATA_DIR = f'{ROOT}/task_dim/preprocessed_data'
VOL_DATA_DIR = f"{ROOT}/task_dim/StudyForrest/data"
SURFACE_RESOLUTION = 10242
NODES_LH = 9372
NODES_RH = 9370
SEARCHLIGHT_RADIUS = 20 
TIMEPOINTS = {'objectcategories':156*4,
              'movie':3599}
RUNS={'localizer':4,
              'movie':8}

SESSIONS2TASK = {'localizer': 'objectcategories', 'movie': 'movie'}

FEATURES_FILES = {'demo':'../data/sherlock/behavioral_data/sherlock_labels_coded_expanded.csv',
                   'sherlock':'../data/sherlock/behavioral_data/sherlock_labels_coded_expanded.csv',
                   'forrest':'../data/StudyForrest/behavioral_data/forrest_movie_labels_coded_expanded.csv'}

FEATURES_FILES_ORIGINAL = {'sherlock':'../data/sherlock/behavioral_data/Sherlock_Segments_master.csv',
                    'forrest':'../data/StudyForrest/behavioral_data/ForrestGumpAnnotations.csv'}

EMBEDDING_METHODS = ['PHATE', 'TPHATE', 'UMAP', 'PCA', "TSNE"]

# SUBJECTS  = [1,2,3,4,6,9,10,14,15,16,17,18,19,20]
SUBJECTS  = [1,2,3,4,9,10,14,15,16,17,18,19,20]

REGRESSOR_NAMES = {'movie':['IoE_coded','FoT_coded']}

#### CONFIG INFORMATION FOR REST_MOVIE



REST_DIR="/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Rest/preprocessed_standard/nonlinear_alignment/"
AERONAUT_DIR="/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Aeronaut/preprocessed_standard/nonlinear_alignment/"
MICKEY_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Mickey/preprocessed_standard/nonlinear_alignment/'
LK_CARTOON_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/LionKing_Cartoon/preprocessed_standard/nonlinear_alignment/' # appears to be not formatted
LK_LA_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/LionKing_Live/preprocessed_standard/nonlinear_alignment/' # appears to be not formatted

RM_DATA_DIRS={'REST':REST_DIR, 'AERONAUT':AERONAUT_DIR, 'MICKEY':MICKEY_DIR, 'LK_CARTOON':LK_CARTOON_DIR, "LK_LA":LK_LA_DIR}
RM_TIMEPOINTS={'REST':152, 'AERONAUT':93, 'MICKEY':74, 'LK_CARTOON':93, 'LK_LA':93}

RM_MASKS={'REST':'./masks/Adult_Rest_intersect_mask.nii.gz', 'AERONAUT':'./masks/Adult_Aeronaut_intersect_mask.nii.gz', 'MICKEY':'./masks/Adult_Mickey_intersect_mask.nii.gz'}

RM_SUBJECTS = {'REST':np.arange(1,13),'MICKEY':[1,2,3,4,5,7,8,9,10,11,12], 'AERONAUT':np.arange(1,13)}

### CONFIG INFO FOR NARRATIVES ##
BASE_DIR_NARRATIVES = '/gpfs/milgram/project/turk-browne/projects/Narratives'
NARRATIVES_DATA_DIRS = {'BLACK':join(BASE_DIR_NARRATIVES, 'black'), 'PIEMANPNI':join(BASE_DIR_NARRATIVES, 'piemanpni'), 'BRONX':join(BASE_DIR_NARRATIVES, 'bronx'), 'FORGOT':join(BASE_DIR_NARRATIVES, 'forgot')}
NARRATIVES_SUBJECTS = [127, 265, 267, 272, 273, 274, 275, 276, 277, 279, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315]
NARRATIVES_TIMEPOINTS={'BLACK':550, 'BRONX':390, 'FORGOT':574, 'PIEMANPNI':294}

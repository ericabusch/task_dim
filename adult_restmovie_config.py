# adult rest movie config
from os.path import join
import os

NJOBS=16
VERBOSE=True
# check if running on milgram, misha, or local
if 'milgram' in os.uname()[1]:
    ROOT = 'ROOTPATH' # keep cluster paths private
    SCRATCH_DIR = f'SCRATCHPATH/task_dim_sandbox'
elif os.path.exists('/gpfs/radev'):
    ROOT = 'ROOTPATH'
    SCRATCH_DIR = f'SCRATCHPATH/task_dim_sandbox'
else:
    _repo_dir = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(_repo_dir)
    SCRATCH_DIR = os.path.join(_repo_dir, 'scratch')


KNN=5
THRESHOLD=0.9
IDE_METHODS = ['TPHATE_DiffOp_IDE', 'PHATE_DiffOp_IDE', 'PCA', 'MLE', 'MiND_ML', 'lPCA']

#### Adult rest-movie parameters
DATASET_NAME='adult_restmovie'
BASE_DIR_RM='PATH_TO_DATASET' # replace with the path to the dataset; keep cluster paths private
REST_DIR=f"{BASE_DIR_RM}/Adult_Rest/preprocessed_standard/nonlinear_alignment/"
AERONAUT_DIR=f"{BASE_DIR_RM}/Adult_Aeronaut/preprocessed_standard/nonlinear_alignment/"
MICKEY_DIR=f"{BASE_DIR_RM}/Adult_Mickey/preprocessed_standard/nonlinear_alignment/"
RM_DATA_DIRS={'rest':REST_DIR, 'aeronaut':AERONAUT_DIR, 'mickey':MICKEY_DIR}
RM_TIMEPOINTS={'rest':152, 'aeronaut':93, 'mickey':74}
RM_MASKS={K:f'{ROOT}/task_dim/masks/Adult_{K.lower().capitalize()}_intersect_mask.nii.gz' for K in RM_DATA_DIRS.keys()}
RM_SUBJECTS = [f'rest_movie_{i:02d}' for i in [1,2,3,4,5,6,7,8,9,10,11,12]] 
RM_OUTDIR = f'{ROOT}/task_dim/adult_restmovie'
RM_STRING_MATCH = '*_fslmotion_thr0.2_Only.nii.gz'
RM_INTERSECT_MASK = f'{ROOT}/task_dim/adult_restmovie/masks/adult_restmovie_intersect_mask.nii.gz'
RM_RESULTS_DIR = f'{ROOT}/task_dim/adult_restmovie/results/'
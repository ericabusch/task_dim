# adult rest movie config
from os.path import join

NJOBS=16
VERBOSE=True
ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
KNN=5
THRESHOLD=0.9
IDE_METHODS = ['TPHATE_DiffOp_IDE','TPHATE_VNE_IDE', 'PHATE_VNE_IDE','PCA','MLE']

#### Adult rest-movie parameters
DATASET_NAME='adult_restmovie'
BASE_DIR_RM='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/'
REST_DIR="/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Rest/preprocessed_standard/nonlinear_alignment/"
AERONAUT_DIR="/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Aeronaut/preprocessed_standard/nonlinear_alignment/"
MICKEY_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/RestingState/Adult_Mickey/preprocessed_standard/nonlinear_alignment/'
LK_CARTOON_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/LionKing_Cartoon/preprocessed_standard/nonlinear_alignment/' # appears to be not formatted
LK_LA_DIR='/gpfs/milgram/project/turk-browne/projects/dev_neuropipe/data/Movies/LionKing_Live/preprocessed_standard/nonlinear_alignment/' # appears to be not formatted
RM_DATA_DIRS={'rest':REST_DIR, 'aeronaut':AERONAUT_DIR, 'mickey':MICKEY_DIR}
RM_TIMEPOINTS={'rest':152, 'aeronaut':93, 'mickey':74, 'LK_CARTOON':93, 'LK_LA':93}
RM_MASKS={K:f'{ROOT}/task_dim/masks/Adult_{K.lower().capitalize()}_intersect_mask.nii.gz' for K in RM_DATA_DIRS.keys()}
RM_SUBJECTS = [f'rest_movie_{i:02d}' for i in [1,2,3,4,5,7,8,9,10,11,12]] # subject 6 does not have mickey
RM_OUTDIR = f'{ROOT}/task_dim/adult_restmovie'
RM_STRING_MATCH = '*_fslmotion_thr0.2_Only.nii.gz'
RM_INTERSECT_MASK = f'{ROOT}/task_dim/adult_restmovie/masks/adult_restmovie_intersect_mask.nii.gz'
RM_RESULTS_DIR = f'{ROOT}/task_dim/adult_restmovie/results/'
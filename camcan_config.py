# camcan config
from os.path import join

NJOBS=16
VERBOSE=True
ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
KNN=5
THRESHOLD=0.9
IDE_METHODS = ['TPHATE_DiffOp_IDE', 'MiND_ML', 'lPCA','PCA','MLE']

########################################
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

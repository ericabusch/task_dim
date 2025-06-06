from os.path import join

NJOBS=16
VERBOSE=True
ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
KNN=5
THRESHOLD=0.85
IDE_METHODS = ['TPHATE_DiffOp_IDE','PCA']

### CONFIG INFO FOR NARRATIVES ##
BASE_DIR_NARRATIVES = '/gpfs/milgram/project/turk-browne/projects/Narratives'
NARRATIVES_DATALAD_DIR='/gpfs/milgram/scratch60/turk-browne/elb77/Narratives/narratives'
NARRATIVES_DATA_DIRS = {'black':join(BASE_DIR_NARRATIVES, 'black'),
                        'piemanpni':join(BASE_DIR_NARRATIVES, 'piemanpni'), 
                        'bronx':join(BASE_DIR_NARRATIVES, 'bronx'),
                        'forgot':join(BASE_DIR_NARRATIVES, 'forgot')}
NARRATIVES_SUBJECTS = [127, 265, 267, 272, 273, 274, 275, 276, 277, 279, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 
291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315]
NARRATIVES_SUBJECTS = [f'sub-{s}' for s in NARRATIVES_SUBJECTS]
exclude = ['sub-309','sub-306','sub-303','sub-305','sub-298']
NARRATIVES_SUBJECTS = [x for x in NARRATIVES_SUBJECTS if x not in exclude]

NARRATIVES_TIMEPOINTS={'black':550, 'bronx':390, 'forgot':574, 'piemanpni':294}
NARRATIVES_OUTDIR = f'{ROOT}/task_dim/Narratives'
NARRATIVES_RESULTS_DIR = f'{ROOT}/task_dim/Narratives/results'
NARRATIVES_INTERSECT_MASK=f'{ROOT}/task_dim/Narratives/masks/Narratives_intersect_mask.nii.gz'
from os.path import join

NJOBS=16
VERBOSE=True
ROOT = '/gpfs/milgram/project/turk-browne/users/elb77/'
SCRATCH_DIR = '/gpfs/milgram/scratch60/turk-browne/elb77/task_dim_sandbox'
KNN=10
THRESHOLD=0.9
IDE_METHODS = ['TPHATE_DiffOp_IDE','PCA']
BASE_DIR_PARTLY_CLOUDY = '/gpfs/milgram/project/turk-browne/projects/partly_recon'
PC_SUBJECTS = [f'sub-pixar{i:03d}' for i in range(1,156)]
PC_DATA_DIR = f'{BASE_DIR_PARTLY_CLOUDY}/data/resampled_participants/motion_reg/'
PC_INTERSECT_MASK=f'{ROOT}/task_dim/PartlyCloudy/masks/PartlyCloudy_intersect_mask.nii.gz'
FMRIPREP_DIR='/gpfs/milgram/data/PartlyCloudy/preprocessed/fmriprep'
PC_OUTDIR = f'{ROOT}/task_dim/PartlyCloudy/'
PC_RESULTS_DIR=f'{PC_OUTDIR}/results'
PC_PARTICIPANT_DF=f'{PC_OUTDIR}/participants.csv'
#PC_AGE_GROUPS = ['3yo','4yo','5yo','7yo','8-12yo','Adult']
PC_AGE_GROUPS = ['U05', 'U06', 'U082', 'U13', 'Adult']